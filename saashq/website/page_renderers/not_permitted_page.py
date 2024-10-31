import saashq
from saashq import _
from saashq.utils import cstr
from saashq.website.page_renderers.template_page import TemplatePage


class NotPermittedPage(TemplatePage):
	def __init__(self, path=None, http_status_code=None, exception=""):
		saashq.local.message = cstr(exception)
		super().__init__(path=path, http_status_code=http_status_code)
		self.http_status_code = 403

	def can_render(self):
		return True

	def render(self):
		action = f"/login?redirect-to={saashq.request.path}"
		if saashq.request.path.startswith("/app/") or saashq.request.path == "/app":
			action = "/login"
		saashq.local.message_title = _("Not Permitted")
		saashq.local.response["context"] = dict(
			indicator_color="red", primary_action=action, primary_label=_("Login"), fullpage=True
		)
		self.set_standard_path("message")
		return super().render()
