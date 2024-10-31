import saashq
from saashq.website.page_renderers.template_page import TemplatePage


class PrintPage(TemplatePage):
	"""
	default path returns a printable object (based on permission)
	/Quotation/Q-0001
	"""

	def can_render(self):
		parts = self.path.split("/", 1)
		if len(parts) == 2:
			if saashq.db.exists("DocType", parts[0], True) and saashq.db.exists(parts[0], parts[1], True):
				return True

		return False

	def render(self):
		parts = self.path.split("/", 1)
		saashq.form_dict.doctype = parts[0]
		saashq.form_dict.name = parts[1]
		self.set_standard_path("printview")
		return super().render()
