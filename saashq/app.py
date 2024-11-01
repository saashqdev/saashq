# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import functools
import gc
import logging
import os
import re

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.http import generate_etag, is_resource_modified, quote_etag
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator

import saashq
import saashq.api
import saashq.handler
import saashq.monitor
import saashq.rate_limiter
import saashq.recorder
import saashq.utils.response
from saashq import _
from saashq.auth import SAFE_HTTP_METHODS, UNSAFE_HTTP_METHODS, HTTPRequest, validate_auth
from saashq.middlewares import StaticDataMiddleware
from saashq.utils import CallbackManager, cint, get_site_name
from saashq.utils.data import escape_html
from saashq.utils.error import log_error_snapshot
from saashq.website.serve import get_response

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")


# If gc.freeze is done then importing modules before forking allows us to share the memory
if saashq._tune_gc:
	import gettext

	import babel
	import babel.messages
	import bleach
	import num2words
	import pydantic

	import saashq.boot
	import saashq.client
	import saashq.core.doctype.file.file
	import saashq.core.doctype.user.user
	import saashq.database.mariadb.database  # Load database related utils
	import saashq.database.query
	import saashq.desk.desktop  # workspace
	import saashq.desk.form.save
	import saashq.model.db_query
	import saashq.query_builder
	import saashq.utils.background_jobs  # Enqueue is very common
	import saashq.utils.data  # common utils
	import saashq.utils.jinja  # web page rendering
	import saashq.utils.jinja_globals
	import saashq.utils.redis_wrapper  # Exact redis_wrapper
	import saashq.utils.safe_exec
	import saashq.utils.typing_validations  # any whitelisted method uses this
	import saashq.website.path_resolver  # all the page types and resolver
	import saashq.website.router  # Website router
	import saashq.website.website_generator  # web page doctypes

# end: module pre-loading


def after_response_wrapper(app):
	"""Wrap a WSGI application to call after_response hooks after we have responded.

	This is done to reduce response time by deferring expensive tasks."""

	@functools.wraps(app)
	def application(environ, start_response):
		return ClosingIterator(
			app(environ, start_response),
			(
				saashq.rate_limiter.update,
				saashq.recorder.dump,
				saashq.request.after_response.run,
				saashq.destroy,
			),
		)

	return application


@after_response_wrapper
@Request.application
def application(request: Request):
	response = None

	try:
		rollback = True

		init_request(request)

		validate_auth()

		if request.method == "OPTIONS":
			response = Response()

		elif saashq.form_dict.cmd:
			from saashq.deprecation_dumpster import deprecation_warning

			deprecation_warning(
				"unknown",
				"v17",
				f"{saashq.form_dict.cmd}: Sending `cmd` for RPC calls is deprecated, call REST API instead `/api/method/cmd`",
			)
			saashq.handler.handle()
			response = saashq.utils.response.build_response("json")

		elif request.path.startswith("/api/"):
			response = saashq.api.handle(request)

		elif request.path.startswith("/backups"):
			response = saashq.utils.response.download_backup(request.path)

		elif request.path.startswith("/private/files/"):
			response = saashq.utils.response.download_private_file(request.path)

		elif request.method in ("GET", "HEAD", "POST"):
			response = get_response()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = sync_database(rollback)

	finally:
		# Important note:
		# this function *must* always return a response, hence any exception thrown outside of
		# try..catch block like this finally block needs to be handled appropriately.

		if rollback and request.method in UNSAFE_HTTP_METHODS and saashq.db:
			saashq.db.rollback()

		try:
			run_after_request_hooks(request, response)
		except Exception:
			# We can not handle exceptions safely here.
			saashq.logger().error("Failed to run after request hook", exc_info=True)

	log_request(request, response)
	# return 304 if unmodified
	if not response.direct_passthrough:
		etag = generate_etag(response.data)
		if not is_resource_modified(request.environ, etag):
			return Response(status=304, headers={"ETag": quote_etag(etag)})
	process_response(response)

	return response


def run_after_request_hooks(request, response):
	if not getattr(saashq.local, "initialised", False):
		return

	for after_request_task in saashq.get_hooks("after_request"):
		saashq.call(after_request_task, response=response, request=request)


def init_request(request):
	saashq.local.request = request
	saashq.local.request.after_response = CallbackManager()

	saashq.local.is_ajax = saashq.get_request_header("X-Requested-With") == "XMLHttpRequest"

	site = _site or request.headers.get("X-Saashq-Site-Name") or get_site_name(request.host)
	saashq.init(site, sites_path=_sites_path, force=True)

	if not (saashq.local.conf and saashq.local.conf.db_name):
		# site does not exist
		raise NotFound

	if saashq.local.conf.maintenance_mode:
		saashq.connect()
		if saashq.local.conf.allow_reads_during_maintenance:
			setup_read_only_mode()
		else:
			raise saashq.SessionStopped("Session Stopped")
	else:
		saashq.connect(set_admin_as_user=False)
	if request.path.startswith("/api/method/upload_file"):
		from saashq.core.api.file import get_max_file_size

		request.max_content_length = get_max_file_size()
	else:
		request.max_content_length = cint(saashq.local.conf.get("max_file_size")) or 25 * 1024 * 1024
	make_form_dict(request)

	if request.method != "OPTIONS":
		saashq.local.http_request = HTTPRequest()

	for before_request_task in saashq.get_hooks("before_request"):
		saashq.call(before_request_task)


def setup_read_only_mode():
	"""During maintenance_mode reads to DB can still be performed to reduce downtime. This
	function sets up read only mode

	- Setting global flag so other pages, desk and database can know that we are in read only mode.
	- Setup read only database access either by:
	    - Connecting to read replica if one exists
	    - Or setting up read only SQL transactions.
	"""
	saashq.flags.read_only = True

	# If replica is available then just connect replica, else setup read only transaction.
	if saashq.conf.read_from_replica:
		saashq.connect_replica()
	else:
		saashq.db.begin(read_only=True)


def log_request(request, response):
	if hasattr(saashq.local, "conf") and saashq.local.conf.enable_saashq_logger:
		saashq.logger("saashq.web", allow_site=saashq.local.site).info(
			{
				"site": get_site_name(request.host),
				"remote_addr": getattr(request, "remote_addr", "NOTFOUND"),
				"pid": os.getpid(),
				"user": getattr(saashq.local.session, "user", "NOTFOUND"),
				"base_url": getattr(request, "base_url", "NOTFOUND"),
				"full_path": getattr(request, "full_path", "NOTFOUND"),
				"method": getattr(request, "method", "NOTFOUND"),
				"scheme": getattr(request, "scheme", "NOTFOUND"),
				"http_status_code": getattr(response, "status_code", "NOTFOUND"),
			}
		)


def process_response(response):
	if not response:
		return

	# cache control
	# read: https://simonhearne.com/2022/caching-header-best-practices/
	if saashq.local.response.can_cache:
		response.headers.extend(
			{
				# default: 5m (proxy), 5m (client), 3h (allow stale resources for this long if upstream is down)
				"Cache-Control": "public,s-maxage=300,max-age=300,stale-while-revalidate=10800",
				# for revalidation of a stale resource
				"ETag": quote_etag(generate_etag(response.data)),
			}
		)
	else:
		response.headers.extend(
			{
				"Cache-Control": "no-store,no-cache,must-revalidate,max-age=0",
			}
		)

	# Set cookies, only if response is non-cacheable to avoid proxy cache invalidation
	if hasattr(saashq.local, "cookie_manager") and not saashq.local.response.can_cache:
		saashq.local.cookie_manager.flush_cookies(response=response)

	# rate limiter headers
	if hasattr(saashq.local, "rate_limiter"):
		response.headers.extend(saashq.local.rate_limiter.headers())

	if trace_id := saashq.monitor.get_trace_id():
		response.headers.extend({"X-Saashq-Request-Id": trace_id})

	# CORS headers
	if hasattr(saashq.local, "conf"):
		set_cors_headers(response)


def set_cors_headers(response):
	if not (
		(allowed_origins := saashq.conf.allow_cors)
		and (request := saashq.local.request)
		and (origin := request.headers.get("Origin"))
	):
		return

	if allowed_origins != "*":
		if not isinstance(allowed_origins, list):
			allowed_origins = [allowed_origins]

		if origin not in allowed_origins:
			return

	cors_headers = {
		"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Origin": origin,
		"Vary": "Origin",
	}

	# only required for preflight requests
	if request.method == "OPTIONS":
		cors_headers["Access-Control-Allow-Methods"] = request.headers.get("Access-Control-Request-Method")

		if allowed_headers := request.headers.get("Access-Control-Request-Headers"):
			cors_headers["Access-Control-Allow-Headers"] = allowed_headers

		# allow browsers to cache preflight requests for upto a day
		if not saashq.conf.developer_mode:
			cors_headers["Access-Control-Max-Age"] = "86400"

	response.headers.extend(cors_headers)


def make_form_dict(request: Request):
	import json

	request_data = request.get_data(as_text=True)
	if request_data and request.is_json:
		args = json.loads(request_data)
	else:
		args = {}
		args.update(request.args or {})
		args.update(request.form or {})

	if isinstance(args, dict):
		saashq.local.form_dict = saashq._dict(args)
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		saashq.local.form_dict.pop("_", None)
	elif isinstance(args, list):
		saashq.local.form_dict["data"] = args
	else:
		saashq.throw(_("Invalid request arguments"))


def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	return_as_message = False
	accept_header = saashq.get_request_header("Accept") or ""
	respond_as_json = (
		saashq.get_request_header("Accept")
		and (saashq.local.is_ajax or "application/json" in accept_header)
		or (saashq.local.request.path.startswith("/api/") and not accept_header.startswith("text"))
	)

	allow_traceback = saashq.get_system_settings("allow_error_traceback") if saashq.db else False

	if not saashq.session.user:
		# If session creation fails then user won't be unset. This causes a lot of code that
		# assumes presence of this to fail. Session creation fails => guest or expired login
		# usually.
		saashq.session.user = "Guest"

	if respond_as_json:
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = saashq.utils.response.report_error(http_status_code)

	elif isinstance(e, saashq.SessionStopped):
		response = saashq.utils.response.handle_session_stopped()

	elif (
		http_status_code == 500
		and (saashq.db and isinstance(e, saashq.db.InternalError))
		and (saashq.db and (saashq.db.is_deadlocked(e) or saashq.db.is_timedout(e)))
	):
		http_status_code = 508

	elif http_status_code == 401:
		saashq.respond_as_web_page(
			_("Session Expired"),
			_("Your session has expired, please login again to continue."),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 403:
		saashq.respond_as_web_page(
			_("Not Permitted"),
			_("You do not have enough permissions to complete the action"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 404:
		saashq.respond_as_web_page(
			_("Not Found"),
			_("The resource you are looking for is not available"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 429:
		response = saashq.rate_limiter.respond()

	else:
		traceback = "<pre>" + escape_html(saashq.get_traceback()) + "</pre>"
		# disable traceback in production if flag is set
		if saashq.local.flags.disable_traceback or not allow_traceback and not saashq.local.dev_server:
			traceback = ""

		saashq.respond_as_web_page(
			"Server Error", traceback, http_status_code=http_status_code, indicator_color="red", width=640
		)
		return_as_message = True

	if e.__class__ == saashq.AuthenticationError:
		if hasattr(saashq.local, "login_manager"):
			saashq.local.login_manager.clear_cookies()

	if http_status_code >= 500:
		log_error_snapshot(e)

	if return_as_message:
		response = get_response("message", http_status_code=http_status_code)

	if saashq.conf.get("developer_mode") and not respond_as_json:
		# don't fail silently for non-json response errors
		print(saashq.get_traceback())

	return response


def sync_database(rollback: bool) -> bool:
	# if HTTP method would change server state, commit if necessary
	if saashq.db and (saashq.local.flags.commit or saashq.local.request.method in UNSAFE_HTTP_METHODS):
		saashq.db.commit()
		rollback = False
	elif saashq.db:
		saashq.db.rollback()
		rollback = False

	# update session
	if session := getattr(saashq.local, "session_obj", None):
		if session.update():
			rollback = False

	return rollback


# Always initialize sentry SDK if the DSN is sent
if sentry_dsn := os.getenv("SAASHQ_SENTRY_DSN"):
	import sentry_sdk
	from sentry_sdk.integrations.argv import ArgvIntegration
	from sentry_sdk.integrations.atexit import AtexitIntegration
	from sentry_sdk.integrations.dedupe import DedupeIntegration
	from sentry_sdk.integrations.excepthook import ExcepthookIntegration
	from sentry_sdk.integrations.modules import ModulesIntegration
	from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

	from saashq.utils.sentry import SaashqIntegration, before_send

	integrations = [
		AtexitIntegration(),
		ExcepthookIntegration(),
		DedupeIntegration(),
		ModulesIntegration(),
		ArgvIntegration(),
	]

	experiments = {}
	kwargs = {}

	if os.getenv("ENABLE_SENTRY_DB_MONITORING"):
		integrations.append(SaashqIntegration())
		experiments["record_sql_params"] = True

	if tracing_sample_rate := os.getenv("SENTRY_TRACING_SAMPLE_RATE"):
		kwargs["traces_sample_rate"] = float(tracing_sample_rate)
		application = SentryWsgiMiddleware(application)

	if profiling_sample_rate := os.getenv("SENTRY_PROFILING_SAMPLE_RATE"):
		kwargs["profiles_sample_rate"] = float(profiling_sample_rate)

	sentry_sdk.init(
		dsn=sentry_dsn,
		before_send=before_send,
		attach_stacktrace=True,
		release=saashq.__version__,
		auto_enabling_integrations=False,
		default_integrations=False,
		integrations=integrations,
		_experiments=experiments,
		**kwargs,
	)


def serve(
	port=8000,
	profile=False,
	no_reload=False,
	no_threading=False,
	site=None,
	sites_path=".",
	proxy=False,
):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	if profile or os.environ.get("USE_PROFILER"):
		application = ProfilerMiddleware(application, sort_by=("cumtime", "calls"))

	if not os.environ.get("NO_STATICS"):
		application = application_with_statics()

	if proxy or os.environ.get("USE_PROXY"):
		application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

	application.debug = True
	application.config = {"SERVER_NAME": "127.0.0.1:8000"}

	log = logging.getLogger("werkzeug")
	log.propagate = False

	in_test_env = os.environ.get("CI")
	if in_test_env:
		log.setLevel(logging.ERROR)

	run_simple(
		"0.0.0.0",
		int(port),
		application,
		exclude_patterns=["test_*"],
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading,
	)


def application_with_statics():
	global application, _sites_path

	application = SharedDataMiddleware(application, {"/assets": str(os.path.join(_sites_path, "assets"))})

	application = StaticDataMiddleware(application, {"/files": str(os.path.abspath(_sites_path))})

	return application


# Remove references to pattern that are pre-compiled and loaded to global scopes.
re.purge()

# Both Gunicorn and RQ use forking to spawn workers. In an ideal world, the fork should be sharing
# most of the memory if there are no writes made to data because of Copy on Write, however,
# python's GC is not CoW friendly and writes to data even if user-code doesn't. Specifically, the
# generational GC which stores and mutates every python object: `PyGC_Head`
#
# Calling gc.freeze() moves all the objects imported so far into permanant generation and hence
# doesn't mutate `PyGC_Head`
#
# Refer to issue for more info: https://github.com/saashqdev/saashq/issues/18927
if saashq._tune_gc:
	gc.collect()  # clean up any garbage created so far before freeze
	gc.freeze()
