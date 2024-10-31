# Copyright (c) 2020, Saashq Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import datetime
from collections.abc import Callable
from functools import wraps

import pytz
from werkzeug.wrappers import Response

import saashq
from saashq import _
from saashq.utils import cint


def apply():
	rate_limit = saashq.conf.rate_limit
	if rate_limit:
		saashq.local.rate_limiter = RateLimiter(rate_limit["limit"], rate_limit["window"])
		saashq.local.rate_limiter.apply()


def update():
	if hasattr(saashq.local, "rate_limiter"):
		saashq.local.rate_limiter.update()


def respond():
	if hasattr(saashq.local, "rate_limiter"):
		return saashq.local.rate_limiter.respond()


class RateLimiter:
	def __init__(self, limit, window):
		self.limit = int(limit * 1000000)
		self.window = window

		self.start = datetime.datetime.now(pytz.UTC)
		timestamp = int(saashq.utils.now_datetime().timestamp())

		self.window_number, self.spent = divmod(timestamp, self.window)
		self.key = saashq.cache.make_key(f"rate-limit-counter-{self.window_number}")
		self.counter = cint(saashq.cache.get(self.key))
		self.remaining = max(self.limit - self.counter, 0)
		self.reset = self.window - self.spent

		self.end = None
		self.duration = None
		self.rejected = False

	def apply(self):
		if self.counter > self.limit:
			self.rejected = True
			self.reject()

	def reject(self):
		raise saashq.TooManyRequestsError

	def update(self):
		self.record_request_end()
		pipeline = saashq.cache.pipeline()
		pipeline.incrby(self.key, self.duration)
		pipeline.expire(self.key, self.window)
		pipeline.execute()

	def headers(self):
		self.record_request_end()
		headers = {
			"X-RateLimit-Reset": self.reset,
			"X-RateLimit-Limit": self.limit,
			"X-RateLimit-Remaining": self.remaining,
		}
		if self.rejected:
			headers["Retry-After"] = self.reset
		else:
			headers["X-RateLimit-Used"] = self.duration

		return headers

	def record_request_end(self):
		if self.end is not None:
			return
		self.end = datetime.datetime.now(pytz.UTC)
		self.duration = int((self.end - self.start).total_seconds() * 1000000)

	def respond(self):
		if self.rejected:
			return Response(_("Too Many Requests"), status=429)


def rate_limit(
	key: str | None = None,
	limit: int | Callable = 5,
	seconds: int = 24 * 60 * 60,
	methods: str | list = "ALL",
	ip_based: bool = True,
):
	"""Decorator to rate limit an endpoint.

	This will limit Number of requests per endpoint to `limit` within `seconds`.
	Uses redis cache to track request counts.

	:param key: Key is used to identify the requests uniqueness (Optional)
	:param limit: Maximum number of requests to allow with in window time
	:type limit: Callable or Integer
	:param seconds: window time to allow requests
	:param methods: Limit the validation for these methods.
	        `ALL` is a wildcard that applies rate limit on all methods.
	:type methods: string or list or tuple
	:param ip_based: flag to allow ip based rate-limiting
	:type ip_based: Boolean

	Return: a decorator function that limit the number of requests per endpoint
	"""

	def ratelimit_decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			# Do not apply rate limits if method is not opted to check
			if not saashq.request or (
				methods != "ALL" and saashq.request.method and saashq.request.method.upper() not in methods
			):
				return fn(*args, **kwargs)

			_limit = limit() if callable(limit) else limit

			ip = saashq.local.request_ip if ip_based is True else None

			user_key = saashq.form_dict.get(key, "")

			identity = None

			if key and ip_based:
				identity = ":".join([ip, user_key])

			identity = identity or ip or user_key

			if not identity:
				saashq.throw(_("Either key or IP flag is required."))

			cache_key = saashq.cache.make_key(f"rl:{saashq.form_dict.cmd}:{identity}")

			value = saashq.cache.get(cache_key)
			if not value:
				saashq.cache.setex(cache_key, seconds, 0)

			value = saashq.cache.incrby(cache_key, 1)
			if value > _limit:
				saashq.throw(
					_("You hit the rate limit because of too many requests. Please try after sometime."),
					saashq.RateLimitExceededError,
				)

			return fn(*args, **kwargs)

		return wrapper

	return ratelimit_decorator
