# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import os

import saashq
from saashq import _
from saashq.build import scrub_html_template
from saashq.model.meta import Meta
from saashq.model.utils import render_include
from saashq.modules import get_module_path, load_doctype_module, scrub
from saashq.utils import get_wrench_path, get_html_format
from saashq.utils.data import get_link_to_form

ASSET_KEYS = (
	"__js",
	"__css",
	"__list_js",
	"__calendar_js",
	"__map_js",
	"__linked_with",
	"__messages",
	"__print_formats",
	"__workflow_docs",
	"__form_grid_templates",
	"__listview_template",
	"__tree_js",
	"__dashboard",
	"__kanban_column_fields",
	"__templates",
	"__custom_js",
	"__custom_list_js",
	"__workspaces",
)


def get_meta(doctype, cached=True) -> "FormMeta":
	# don't cache for developer mode as js files, templates may be edited
	cached = cached and not saashq.conf.developer_mode
	if cached:
		meta = saashq.cache.hget("doctype_form_meta", doctype)
		if not meta:
			# Cache miss - explicitly get meta from DB to avoid
			meta = FormMeta(doctype, cached=False)
			saashq.cache.hset("doctype_form_meta", doctype, meta)
	else:
		meta = FormMeta(doctype)

	return meta


class FormMeta(Meta):
	def __init__(self, doctype, *, cached=True):
		self.__dict__.update(saashq.get_meta(doctype, cached=cached).__dict__)
		self.load_assets()

	def load_assets(self):
		if self.get("__assets_loaded", False):
			return

		self.add_search_fields()
		self.add_linked_document_type()

		if not self.istable:
			self.add_code()
			self.add_custom_script()
			self.load_print_formats()
			self.load_workflows()
			self.load_templates()
			self.load_dashboard()
			self.load_kanban_meta()
			self.load_workspaces()

		self.set("__assets_loaded", True)

	def as_dict(self, no_nulls=False):
		d = super().as_dict(no_nulls=no_nulls)

		for k in ASSET_KEYS:
			d[k] = self.get(k)

		# d['fields'] = d.get('fields', [])

		for i, df in enumerate(d.get("fields") or []):
			for k in ("search_fields", "is_custom_field", "linked_document_type"):
				df[k] = self.get("fields")[i].get(k)

		return d

	def add_code(self):
		if self.custom:
			return

		path = os.path.join(get_module_path(self.module), "doctype", scrub(self.name))

		def _get_path(fname):
			return os.path.join(path, scrub(fname))

		system_country = saashq.get_system_settings("country")

		self._add_code(_get_path(self.name + ".js"), "__js")
		if system_country:
			self._add_code(_get_path(os.path.join("regional", system_country + ".js")), "__js")

		self._add_code(_get_path(self.name + ".css"), "__css")
		self._add_code(_get_path(self.name + "_list.js"), "__list_js")
		if system_country:
			self._add_code(_get_path(os.path.join("regional", system_country + "_list.js")), "__list_js")

		self._add_code(_get_path(self.name + "_calendar.js"), "__calendar_js")
		self._add_code(_get_path(self.name + "_tree.js"), "__tree_js")

		listview_template = _get_path(self.name + "_list.html")
		if os.path.exists(listview_template):
			self.set("__listview_template", get_html_format(listview_template))

		self.add_code_via_hook("doctype_js", "__js")
		self.add_code_via_hook("doctype_list_js", "__list_js")
		self.add_code_via_hook("doctype_tree_js", "__tree_js")
		self.add_code_via_hook("doctype_calendar_js", "__calendar_js")
		self.add_html_templates(path)

	def _add_code(self, path, fieldname):
		js = get_js(path)
		if js:
			wrench_path = get_wrench_path() + "/"
			asset_path = path.replace(wrench_path, "")
			comment = f"\n\n/* Adding {asset_path} */\n\n"
			sourceURL = f"\n\n//# sourceURL={scrub(self.name) + fieldname}"
			self.set(fieldname, (self.get(fieldname) or "") + comment + js + sourceURL)

	def add_html_templates(self, path):
		if self.custom:
			return
		templates = dict()
		for fname in os.listdir(path):
			if fname.endswith(".html"):
				with open(os.path.join(path, fname), encoding="utf-8") as f:
					templates[fname.split(".", 1)[0]] = scrub_html_template(f.read())

		self.set("__templates", templates or None)

	def add_code_via_hook(self, hook, fieldname):
		for path in get_code_files_via_hooks(hook, self.name):
			self._add_code(path, fieldname)

	def add_custom_script(self):
		"""embed all require files"""
		# custom script
		client_scripts = (
			saashq.get_all(
				"Client Script",
				filters={"dt": self.name, "enabled": 1},
				fields=["name", "script", "view"],
				order_by="creation asc",
			)
			or ""
		)

		list_script = ""
		form_script = ""
		for script in client_scripts:
			if not script.script:
				continue

			if script.view == "List":
				list_script += f"""
// {script.name}
{script.script}

"""

			elif script.view == "Form":
				form_script += f"""
// {script.name}
{script.script}

"""

		file = scrub(self.name)
		form_script += f"\n\n//# sourceURL={file}__custom_js"
		list_script += f"\n\n//# sourceURL={file}__custom_list_js"

		self.set("__custom_js", form_script)
		self.set("__custom_list_js", list_script)

	def add_search_fields(self):
		"""add search fields found in the doctypes indicated by link fields' options"""
		for df in self.get("fields", {"fieldtype": "Link", "options": ["!=", "[Select]"]}):
			if df.options:
				try:
					search_fields = saashq.get_meta(df.options).search_fields
				except saashq.DoesNotExistError:
					self._show_missing_doctype_msg(df)

				if search_fields:
					search_fields = search_fields.split(",")
					df.search_fields = [sf.strip() for sf in search_fields]

	def _show_missing_doctype_msg(self, df):
		# A link field is referring to non-existing doctype, this usually happens when
		# customizations are removed or some custom app is removed but hasn't cleaned
		# up after itself.
		saashq.clear_last_message()

		msg = _("Field {0} is referring to non-existing doctype {1}.").format(
			saashq.bold(df.fieldname), saashq.bold(df.options)
		)

		if df.get("is_custom_field"):
			custom_field_link = get_link_to_form("Custom Field", df.name)
			msg += " " + _("Please delete the field from {0} or add the required doctype.").format(
				custom_field_link
			)

		saashq.throw(msg, title=_("Missing DocType"))

	def add_linked_document_type(self):
		for df in self.get("fields", {"fieldtype": "Link"}):
			if df.options:
				try:
					df.linked_document_type = saashq.get_meta(df.options).document_type
				except saashq.DoesNotExistError:
					self._show_missing_doctype_msg(df)

	def load_print_formats(self):
		print_formats = saashq.db.sql(
			"""select * FROM `tabPrint Format`
			WHERE doc_type=%s AND docstatus<2 and disabled=0""",
			(self.name,),
			as_dict=1,
			update={"doctype": "Print Format"},
		)

		self.set("__print_formats", print_formats)

	def load_workflows(self):
		# get active workflow
		workflow_name = self.get_workflow()
		workflow_docs = []

		if workflow_name and saashq.db.exists("Workflow", workflow_name):
			workflow = saashq.get_doc("Workflow", workflow_name)
			workflow_docs.append(workflow)

			workflow_docs.extend(saashq.get_doc("Workflow State", d.state) for d in workflow.get("states"))
		self.set("__workflow_docs", workflow_docs)

	def load_templates(self):
		if not self.custom:
			module = load_doctype_module(self.name)
			app = module.__name__.split(".", 1)[0]
			templates = {}
			if hasattr(module, "form_grid_templates"):
				for key, path in module.form_grid_templates.items():
					templates[key] = get_html_format(saashq.get_app_path(app, path))

				self.set("__form_grid_templates", templates)

	def load_dashboard(self):
		self.set("__dashboard", self.get_dashboard_data())

	def load_workspaces(self):
		Shortcut = saashq.qb.DocType("Workspace Shortcut")
		Workspace = saashq.qb.DocType("Workspace")
		shortcut = (
			saashq.qb.from_(Shortcut)
			.select(Shortcut.parent)
			.inner_join(Workspace)
			.on(Workspace.name == Shortcut.parent)
			.where(Shortcut.link_to == self.name)
			.where(Shortcut.type == "DocType")
			.where(Workspace.public == 1)
			.run()
		)
		if shortcut:
			self.set("__workspaces", [shortcut[0][0]])
		else:
			Link = saashq.qb.DocType("Workspace Link")
			link = (
				saashq.qb.from_(Link)
				.select(Link.parent)
				.inner_join(Workspace)
				.on(Workspace.name == Link.parent)
				.where(Link.link_type == "DocType")
				.where(Link.link_to == self.name)
				.where(Workspace.public == 1)
				.run()
			)

			if link:
				self.set("__workspaces", [link[0][0]])

	def load_kanban_meta(self):
		self.load_kanban_column_fields()

	def load_kanban_column_fields(self):
		try:
			values = saashq.get_list(
				"Kanban Board", fields=["field_name"], filters={"reference_doctype": self.name}
			)

			fields = [x["field_name"] for x in values]
			fields = list(set(fields))
			self.set("__kanban_column_fields", fields)
		except saashq.PermissionError:
			# no access to kanban board
			pass


def get_code_files_via_hooks(hook, name):
	code_files = []
	for app_name in saashq.get_installed_apps():
		code_hook = saashq.get_hooks(hook, default={}, app_name=app_name)
		if not code_hook:
			continue

		files = code_hook.get(name, [])
		if not isinstance(files, list):
			files = [files]

		for file in files:
			path = saashq.get_app_path(app_name, *file.strip("/").split("/"))
			code_files.append(path)

	return code_files


def get_js(path):
	js = saashq.read_file(path)
	if js:
		return render_include(js)
