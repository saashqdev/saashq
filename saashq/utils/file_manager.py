# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import base64
import hashlib
import json
import mimetypes
import os
from copy import copy
from urllib.parse import unquote

import saashq
from saashq import _, conf
from saashq.query_builder.utils import DocType
from saashq.utils import call_hook_method, cint, cstr, encode, get_files_path, get_hook_method


class MaxFileSizeReachedError(saashq.ValidationError):
	pass


def safe_b64decode(binary: bytes) -> bytes:
	"""Adds padding if doesn't already exist before decoding.

	This attempts to avoid the `binascii.Error: Incorrect padding` error raised
	when the number of trailing = is simply not enough :crie:. Although, it may
	be an indication of corrupted data.

	Refs:
	        * https://en.wikipedia.org/wiki/Base64
	        * https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
	"""
	return base64.b64decode(binary + b"===")


def get_file_url(file_data_name):
	data = saashq.db.get_value("File", file_data_name, ["file_name", "file_url"], as_dict=True)
	return data.file_url or data.file_name


def upload():
	# get record details
	dt = saashq.form_dict.doctype
	dn = saashq.form_dict.docname
	file_url = saashq.form_dict.file_url
	filename = saashq.form_dict.filename
	saashq.form_dict.is_private = cint(saashq.form_dict.is_private)

	if not filename and not file_url:
		saashq.msgprint(_("Please select a file or url"), raise_exception=True)

	file_doc = get_file_doc()

	comment = {}
	if dt and dn:
		file_url = file_doc.file_url.replace("#", "%23") if file_doc.file_name else file_doc.file_url
		icon = ' <i class="fa fa-lock text-warning"></i>' if file_doc.is_private else ""
		file_name = file_doc.file_name or file_doc.file_url
		comment = saashq.get_doc(dt, dn).add_comment(
			"Attachment",
			f"<a href='{file_url}' target='_blank'>{file_name}</a>{icon}",
		)

	return {
		"name": file_doc.name,
		"file_name": file_doc.file_name,
		"file_url": file_doc.file_url,
		"is_private": file_doc.is_private,
		"comment": comment.as_dict() if comment else {},
	}


def get_file_doc(dt=None, dn=None, folder=None, is_private=None, df=None):
	"""Return File object (Document) from given parameters or `form_dict`."""
	r = saashq.form_dict

	if dt is None:
		dt = r.doctype
	if dn is None:
		dn = r.docname
	if df is None:
		df = r.docfield
	if folder is None:
		folder = r.folder
	if is_private is None:
		is_private = r.is_private

	if r.filedata:
		file_doc = save_uploaded(dt, dn, folder, is_private, df)

	elif r.file_url:
		file_doc = save_url(r.file_url, r.filename, dt, dn, folder, is_private, df)

	return file_doc


def save_uploaded(dt, dn, folder, is_private, df=None):
	fname, content = get_uploaded_content()
	if content:
		return save_file(fname, content, dt, dn, folder, is_private=is_private, df=df)
	else:
		raise Exception


def save_url(file_url, filename, dt, dn, folder, is_private, df=None):
	# if not (file_url.startswith("http://") or file_url.startswith("https://")):
	# 	saashq.msgprint("URL must start with 'http://' or 'https://'")
	# 	return None, None

	file_url = unquote(file_url)
	file_size = saashq.form_dict.file_size

	f = saashq.get_doc(
		{
			"doctype": "File",
			"file_url": file_url,
			"file_name": filename,
			"attached_to_doctype": dt,
			"attached_to_name": dn,
			"attached_to_field": df,
			"folder": folder,
			"file_size": file_size,
			"is_private": is_private,
		}
	)
	f.flags.ignore_permissions = True
	try:
		f.insert()
	except saashq.DuplicateEntryError:
		return saashq.get_doc("File", f.duplicate_entry)
	return f


def get_uploaded_content():
	# should not be unicode when reading a file, hence using saashq.form
	if "filedata" in saashq.form_dict:
		if "," in saashq.form_dict.filedata:
			saashq.form_dict.filedata = saashq.form_dict.filedata.rsplit(",", 1)[1]
		saashq.uploaded_content = safe_b64decode(saashq.form_dict.filedata)
		saashq.uploaded_filename = saashq.form_dict.filename
		return saashq.uploaded_filename, saashq.uploaded_content
	else:
		saashq.msgprint(_("No file attached"))
		return None, None


def save_file(fname, content, dt, dn, folder=None, decode=False, is_private=0, df=None):
	if decode:
		if isinstance(content, str):
			content = content.encode("utf-8")

		if b"," in content:
			content = content.split(b",")[1]
		content = safe_b64decode(content)

	file_size = check_max_file_size(content)
	content_hash = get_content_hash(content)
	content_type = mimetypes.guess_type(fname)[0]
	fname = get_file_name(fname, content_hash[-6:])
	file_data = get_file_data_from_hash(content_hash, is_private=is_private)
	if not file_data:
		call_hook_method("before_write_file", file_size=file_size)

		write_file_method = get_hook_method("write_file", fallback=save_file_on_filesystem)
		file_data = write_file_method(fname, content, content_type=content_type, is_private=is_private)
		file_data = copy(file_data)

	file_data.update(
		{
			"doctype": "File",
			"attached_to_doctype": dt,
			"attached_to_name": dn,
			"attached_to_field": df,
			"folder": folder,
			"file_size": file_size,
			"content_hash": content_hash,
			"is_private": is_private,
		}
	)

	f = saashq.get_doc(file_data)
	f.flags.ignore_permissions = True
	try:
		f.insert()
	except saashq.DuplicateEntryError:
		return saashq.get_doc("File", f.duplicate_entry)

	return f


def get_file_data_from_hash(content_hash, is_private=0):
	for name in saashq.get_all(
		"File", {"content_hash": content_hash, "is_private": is_private}, pluck="name"
	):
		b = saashq.get_doc("File", name)
		return {k: b.get(k) for k in saashq.get_hooks()["write_file_keys"]}
	return False


def save_file_on_filesystem(fname, content, content_type=None, is_private=0):
	fpath = write_file(content, fname, is_private)

	if is_private:
		file_url = f"/private/files/{fname}"
	else:
		file_url = f"/files/{fname}"

	return {"file_name": os.path.basename(fpath), "file_url": file_url}


def get_max_file_size():
	return conf.get("max_file_size") or 10485760


def check_max_file_size(content):
	max_file_size = get_max_file_size()
	file_size = len(content)

	if file_size > max_file_size:
		saashq.msgprint(
			_("File size exceeded the maximum allowed size of {0} MB").format(max_file_size / 1048576),
			raise_exception=MaxFileSizeReachedError,
		)

	return file_size


def write_file(content, fname, is_private=0):
	"""write file to disk with a random name (to compare)"""
	file_path = get_files_path(is_private=is_private)

	# create directory (if not exists)
	saashq.create_folder(file_path)
	# write the file
	if isinstance(content, str):
		content = content.encode()
	with open(os.path.join(file_path.encode("utf-8"), fname.encode("utf-8")), "wb+") as f:
		f.write(content)

	return get_files_path(fname, is_private=is_private)


def remove_all(dt, dn, from_delete=False, delete_permanently=False):
	"""remove all files in a transaction"""
	try:
		for fid in saashq.get_all("File", {"attached_to_doctype": dt, "attached_to_name": dn}, pluck="name"):
			if from_delete:
				# If deleting a doc, directly delete files
				saashq.delete_doc("File", fid, ignore_permissions=True, delete_permanently=delete_permanently)
			else:
				# Removes file and adds a comment in the document it is attached to
				remove_file(
					fid=fid,
					attached_to_doctype=dt,
					attached_to_name=dn,
					from_delete=from_delete,
					delete_permanently=delete_permanently,
				)
	except Exception as e:
		if e.args[0] != 1054:
			raise  # (temp till for patched)


def remove_file(
	fid=None,
	attached_to_doctype=None,
	attached_to_name=None,
	from_delete=False,
	delete_permanently=False,
):
	"""Remove file and File entry"""
	file_name = None
	if not (attached_to_doctype and attached_to_name):
		attached = saashq.db.get_value("File", fid, ["attached_to_doctype", "attached_to_name", "file_name"])
		if attached:
			attached_to_doctype, attached_to_name, file_name = attached

	ignore_permissions, comment = False, None
	if attached_to_doctype and attached_to_name and not from_delete:
		doc = saashq.get_doc(attached_to_doctype, attached_to_name)
		ignore_permissions = saashq.flags.in_web_form or doc.has_permission("write")
		if not file_name:
			file_name = saashq.db.get_value("File", fid, "file_name")
		comment = doc.add_comment("Attachment Removed", file_name)
		saashq.delete_doc(
			"File", fid, ignore_permissions=ignore_permissions, delete_permanently=delete_permanently
		)

	return comment


def delete_file_data_content(doc, only_thumbnail=False):
	method = get_hook_method("delete_file_data_content", fallback=delete_file_from_filesystem)
	method(doc, only_thumbnail=only_thumbnail)


def delete_file_from_filesystem(doc, only_thumbnail=False):
	"""Delete file, thumbnail from File document"""
	if only_thumbnail:
		delete_file(doc.thumbnail_url)
	else:
		delete_file(doc.file_url)
		delete_file(doc.thumbnail_url)


def delete_file(path):
	"""Delete file from `public folder`"""
	if path:
		if ".." in path.split("/"):
			saashq.msgprint(
				_("It is risky to delete this file: {0}. Please contact your System Manager.").format(path)
			)

		parts = os.path.split(path.strip("/"))
		if parts[0] == "files":
			path = saashq.utils.get_site_path("public", "files", parts[-1])

		else:
			path = saashq.utils.get_site_path("private", "files", parts[-1])

		path = encode(path)
		if os.path.exists(path):
			os.remove(path)


def get_file(fname):
	"""Return [`file_name`, `content`] for given file name `fname`."""
	file_path = get_file_path(fname)

	# read the file
	with open(encode(file_path), mode="rb") as f:
		content = f.read()
		try:
			# for plain text files
			content = content.decode()
		except UnicodeDecodeError:
			# for .png, .jpg, etc
			pass

	return [file_path.rsplit("/", 1)[-1], content]


def get_file_path(file_name):
	"""Return file path from given file name."""
	if "../" in file_name:
		return

	File = DocType("File")

	f = (
		saashq.qb.from_(File)
		.where((File.name == file_name) | (File.file_name == file_name))
		.select(File.file_url)
		.run()
	)

	if f:
		file_name = f[0][0]

	file_path = file_name

	if "/" not in file_path:
		file_path = "/files/" + file_path

	if file_path.startswith("/private/files/"):
		file_path = get_files_path(*file_path.split("/private/files/", 1)[1].split("/"), is_private=1)

	elif file_path.startswith("/files/"):
		file_path = get_files_path(*file_path.split("/files/", 1)[1].split("/"))

	else:
		saashq.throw(_("There is some problem with the file url: {0}").format(file_path))

	return file_path


def get_content_hash(content):
	if isinstance(content, str):
		content = content.encode()
	return hashlib.md5(content, usedforsecurity=False).hexdigest()


def get_file_name(fname, optional_suffix):
	# convert to unicode
	fname = cstr(fname)

	n_records = saashq.get_all("File", {"file_name": fname}, pluck="name")
	if len(n_records) > 0 or os.path.exists(encode(get_files_path(fname))):
		f = fname.rsplit(".", 1)
		if len(f) == 1:
			partial, extn = f[0], ""
		else:
			partial, extn = f[0], "." + f[1]
		return f"{partial}{optional_suffix}{extn}"
	return fname


@saashq.whitelist()
def add_attachments(doctype, name, attachments):
	"""Add attachments to the given DocType"""
	if isinstance(attachments, str):
		attachments = json.loads(attachments)
	# loop through attachments
	files = []
	for a in attachments:
		if isinstance(a, str):
			attach = saashq.db.get_value(
				"File", {"name": a}, ["file_name", "file_url", "is_private"], as_dict=1
			)
			# save attachments to new doc
			f = save_url(
				attach.file_url, attach.file_name, doctype, name, "Home/Attachments", attach.is_private
			)
			files.append(f)

	return files


def is_safe_path(path: str) -> bool:
	if path.startswith(("http://", "https://")):
		return True

	basedir = saashq.get_site_path()
	# ref: https://docs.python.org/3/library/os.path.html#os.path.commonpath
	matchpath = os.path.abspath(path)
	basedir = os.path.abspath(basedir)

	return basedir == os.path.commonpath((basedir, matchpath))
