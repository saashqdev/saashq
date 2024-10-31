import http
import json
import os
import uuid
from io import BytesIO

from pypdf import PdfWriter

import saashq
from saashq import _
from saashq.core.doctype.access_log.access_log import make_access_log
from saashq.translate import print_language
from saashq.utils.pdf import get_pdf

no_cache = 1

base_template_path = "www/printview.html"
standard_format = "templates/print_formats/standard.html"

from saashq.www.printview import validate_print_permission


@saashq.whitelist()
def download_multi_pdf(
	doctype: str | dict[str, list[str]],
	name: str | list[str],
	format: str | None = None,
	no_letterhead: bool = False,
	letterhead: str | None = None,
	options: str | None = None,
):
	"""
	Calls _download_multi_pdf with the given parameters and returns the response
	"""
	return _download_multi_pdf(doctype, name, format, no_letterhead, letterhead, options)


@saashq.whitelist()
def download_multi_pdf_async(
	doctype: str | dict[str, list[str]],
	name: str | list[str],
	format: str | None = None,
	no_letterhead: bool = False,
	letterhead: str | None = None,
	options: str | None = None,
):
	"""
	Calls _download_multi_pdf with the given parameters in a background job, returns task ID
	"""
	task_id = str(uuid.uuid4())
	if isinstance(doctype, dict):
		doc_count = sum([len(doctype[dt]) for dt in doctype])
	else:
		doc_count = len(json.loads(name))

	saashq.enqueue(
		_download_multi_pdf,
		doctype=doctype,
		name=name,
		task_id=task_id,
		format=format,
		no_letterhead=no_letterhead,
		letterhead=letterhead,
		options=options,
		queue="long" if doc_count > 20 else "short",
	)
	saashq.local.response["http_status_code"] = http.HTTPStatus.CREATED
	return {"task_id": task_id}


def _download_multi_pdf(
	doctype: str | dict[str, list[str]],
	name: str | list[str],
	format: str | None = None,
	no_letterhead: bool = False,
	letterhead: str | None = None,
	options: str | None = None,
	task_id: str | None = None,
):
	"""Return a PDF compiled by concatenating multiple documents.

	The documents can be from a single DocType or multiple DocTypes.

	Note: The design may seem a little weird, but it  exists to ensure backward compatibility.
	          The correct way to use this function is to pass a dict to doctype as described below

	NEW FUNCTIONALITY
	=================
	Parameters:
	doctype (dict):
	        key (string): DocType name
	        value (list): of strings of doc names which need to be concatenated and printed
	name (string):
	        name of the pdf which is generated
	format:
	        Print Format to be used

	OLD FUNCTIONALITY - soon to be deprecated
	=========================================
	Parameters:
	doctype (string):
	        name of the DocType to which the docs belong which need to be printed
	name (string or list):
	        If string the name of the doc which needs to be printed
	        If list the list of strings of doc names which needs to be printed
	format:
	        Print Format to be used

	Returns:
	Publishes a link to the PDF to the given task ID
	"""
	filename = ""

	pdf_writer = PdfWriter()

	if isinstance(options, str):
		options = json.loads(options)

	if not isinstance(doctype, dict):
		result = json.loads(name)
		total_docs = len(result)
		filename = f"{doctype}_"

		# Concatenating pdf files
		for idx, ss in enumerate(result):
			try:
				pdf_writer = saashq.get_print(
					doctype,
					ss,
					format,
					as_pdf=True,
					output=pdf_writer,
					no_letterhead=no_letterhead,
					letterhead=letterhead,
					pdf_options=options,
				)
			except Exception:
				if task_id:
					saashq.publish_realtime(task_id=task_id, message={"message": "Failed"})

			# Publish progress
			if task_id:
				saashq.publish_progress(
					percent=(idx + 1) / total_docs * 100,
					title=_("PDF Generation in Progress"),
					description=_("{0}/{1} complete | Please leave this tab open until completion.").format(
						idx + 1, total_docs
					),
					task_id=task_id,
				)

		if task_id is None:
			saashq.local.response.filename = "{doctype}.pdf".format(
				doctype=doctype.replace(" ", "-").replace("/", "-")
			)

	else:
		total_docs = sum([len(doctype[dt]) for dt in doctype])
		count = 1
		for doctype_name in doctype:
			filename += f"{doctype_name}_"
			for doc_name in doctype[doctype_name]:
				try:
					pdf_writer = saashq.get_print(
						doctype_name,
						doc_name,
						format,
						as_pdf=True,
						output=pdf_writer,
						no_letterhead=no_letterhead,
						letterhead=letterhead,
						pdf_options=options,
					)
				except Exception:
					if task_id:
						saashq.publish_realtime(task_id=task_id, message="Failed")
					saashq.log_error(
						title="Error in Multi PDF download",
						message=f"Permission Error on doc {doc_name} of doctype {doctype_name}",
						reference_doctype=doctype_name,
						reference_name=doc_name,
					)

				count += 1

				if task_id:
					saashq.publish_progress(
						percent=count / total_docs * 100,
						title=_("PDF Generation in Progress"),
						description=_(
							"{0}/{1} complete | Please leave this tab open until completion."
						).format(count, total_docs),
						task_id=task_id,
					)
		if task_id is None:
			saashq.local.response.filename = f"{name}.pdf"

	with BytesIO() as merged_pdf:
		pdf_writer.write(merged_pdf)
		if task_id:
			_file = saashq.get_doc(
				{
					"doctype": "File",
					"file_name": f"{filename}{task_id}.pdf",
					"content": merged_pdf.getvalue(),
					"is_private": 1,
				}
			)
			_file.save()
			saashq.publish_realtime(f"task_complete:{task_id}", message={"file_url": _file.unique_url})
		else:
			saashq.local.response.filecontent = merged_pdf.getvalue()
			saashq.local.response.type = "pdf"


from saashq.deprecation_dumpster import read_multi_pdf


@saashq.whitelist(allow_guest=True)
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None):
	doc = doc or saashq.get_doc(doctype, name)
	validate_print_permission(doc)

	with print_language(language):
		pdf_file = saashq.get_print(
			doctype, name, format, doc=doc, as_pdf=True, letterhead=letterhead, no_letterhead=no_letterhead
		)

	saashq.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
	saashq.local.response.filecontent = pdf_file
	saashq.local.response.type = "pdf"


@saashq.whitelist()
def report_to_pdf(html, orientation="Landscape"):
	make_access_log(file_type="PDF", method="PDF", page=html)
	saashq.local.response.filename = "report.pdf"
	saashq.local.response.filecontent = get_pdf(html, {"orientation": orientation})
	saashq.local.response.type = "pdf"


@saashq.whitelist()
def print_by_server(
	doctype, name, printer_setting, print_format=None, doc=None, no_letterhead=0, file_path=None
):
	print_settings = saashq.get_doc("Network Printer Settings", printer_setting)
	try:
		import cups
	except ImportError:
		saashq.throw(_("You need to install pycups to use this feature!"))

	try:
		cups.setServer(print_settings.server_ip)
		cups.setPort(print_settings.port)
		conn = cups.Connection()
		output = PdfWriter()
		output = saashq.get_print(
			doctype, name, print_format, doc=doc, no_letterhead=no_letterhead, as_pdf=True, output=output
		)
		if not file_path:
			file_path = os.path.join("/", "tmp", f"saashq-pdf-{saashq.generate_hash()}.pdf")
		output.write(open(file_path, "wb"))
		conn.printFile(print_settings.printer_name, file_path, name, {})
	except OSError as e:
		if (
			"ContentNotFoundError" in e.message
			or "ContentOperationNotPermittedError" in e.message
			or "UnknownContentError" in e.message
			or "RemoteHostClosedError" in e.message
		):
			saashq.throw(_("PDF generation failed"))
	except cups.IPPError:
		saashq.throw(_("Printing failed"))
