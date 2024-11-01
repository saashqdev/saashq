# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import saashq
from saashq import _
from saashq.core.doctype.custom_docperm.custom_docperm import update_custom_docperm
from saashq.model.document import Document
from saashq.permissions import add_permission, add_user_permission
from saashq.utils import get_link_to_form
from saashq.utils.modules import get_modules_from_app


class UserType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.user_document_type.user_document_type import UserDocumentType
		from saashq.core.doctype.user_select_document_type.user_select_document_type import (
			UserSelectDocumentType,
		)
		from saashq.core.doctype.user_type_module.user_type_module import UserTypeModule
		from saashq.types import DF

		apply_user_permission_on: DF.Link | None
		custom_select_doctypes: DF.Table[UserSelectDocumentType]
		is_standard: DF.Check
		role: DF.Link | None
		select_doctypes: DF.Table[UserSelectDocumentType]
		user_doctypes: DF.Table[UserDocumentType]
		user_id_field: DF.Literal[None]
		user_type_modules: DF.Table[UserTypeModule]
	# end: auto-generated types

	def validate(self):
		self.set_modules()
		self.add_select_perm_doctypes()

	def clear_cache(self):
		super().clear_cache()

		if not self.is_standard:
			saashq.cache.delete_value("non_standard_user_types")

	def on_update(self):
		if self.is_standard:
			return

		self.validate_document_type_limit()
		self.validate_role()
		self.add_role_permissions_for_user_doctypes()
		self.add_role_permissions_for_select_doctypes()
		self.add_role_permissions_for_file()
		self.update_users()
		self.remove_permission_for_deleted_doctypes()

	def on_trash(self):
		if self.is_standard:
			saashq.throw(_("Standard user type {0} can not be deleted.").format(saashq.bold(self.name)))

	def set_modules(self):
		if not self.user_doctypes:
			return

		modules = saashq.get_all(
			"DocType",
			filters={"name": ("in", [d.document_type for d in self.user_doctypes])},
			distinct=True,
			pluck="module",
		)

		self.set("user_type_modules", [])
		for module in modules:
			self.append("user_type_modules", {"module": module})

	def validate_document_type_limit(self):
		limit = saashq.conf.get("user_type_doctype_limit", {}).get(saashq.scrub(self.name))

		if not limit and saashq.session.user != "Administrator":
			saashq.throw(
				_("User does not have permission to create the new {0}").format(saashq.bold(_("User Type"))),
				title=_("Permission Error"),
			)

		if not limit:
			saashq.throw(
				_("The limit has not set for the user type {0} in the site config file.").format(
					saashq.bold(self.name)
				),
				title=_("Set Limit"),
			)

		if self.user_doctypes and len(self.user_doctypes) > limit:
			saashq.throw(
				_("The total number of user document types limit has been crossed."),
				title=_("User Document Types Limit Exceeded"),
			)

		custom_doctypes = [row.document_type for row in self.user_doctypes if row.is_custom]
		if custom_doctypes and len(custom_doctypes) > 3:
			saashq.throw(
				_("You can only set the 3 custom doctypes in the Document Types table."),
				title=_("Custom Document Types Limit Exceeded"),
			)

	def validate_role(self):
		if not self.role:
			saashq.throw(_("The field {0} is mandatory").format(saashq.bold(_("Role"))))

		if not saashq.db.get_value("Role", self.role, "is_custom"):
			saashq.throw(
				_("The role {0} should be a custom role.").format(
					saashq.bold(get_link_to_form("Role", self.role))
				)
			)

	def update_users(self):
		for row in saashq.get_all("User", filters={"user_type": self.name}):
			user = saashq.get_cached_doc("User", row.name)
			self.update_roles_in_user(user)
			self.update_modules_in_user(user)
			user.update_children()

	def update_roles_in_user(self, user):
		user.set("roles", [])
		user.append("roles", {"role": self.role})

	def update_modules_in_user(self, user):
		block_modules = saashq.get_all(
			"Module Def",
			fields=["name as module"],
			filters={"name": ["not in", [d.module for d in self.user_type_modules]]},
		)

		if block_modules:
			user.set("block_modules", block_modules)

	def add_role_permissions_for_user_doctypes(self):
		perms = ["read", "write", "create", "submit", "cancel", "amend", "delete", "print", "email", "share"]
		for row in self.user_doctypes:
			docperm = add_role_permissions(row.document_type, self.role)
			values = {perm: row.get(perm, default=0) for perm in perms}

			update_custom_docperm(docperm, values)

	def add_select_perm_doctypes(self):
		if saashq.flags.ignore_select_perm:
			return

		self.select_doctypes = []

		select_doctypes = []
		user_doctypes = [row.document_type for row in self.user_doctypes]

		for doctype in user_doctypes:
			doc = saashq.get_meta(doctype)
			self.prepare_select_perm_doctypes(doc, user_doctypes, select_doctypes)

			for child_table in doc.get_table_fields():
				child_doc = saashq.get_meta(child_table.options)
				if child_doc:
					self.prepare_select_perm_doctypes(child_doc, user_doctypes, select_doctypes)

		if select_doctypes:
			select_doctypes = set(select_doctypes)
			for select_doctype in select_doctypes:
				self.append("select_doctypes", {"document_type": select_doctype})

	def prepare_select_perm_doctypes(self, doc, user_doctypes, select_doctypes):
		for field in doc.get_link_fields():
			if field.options not in user_doctypes:
				select_doctypes.append(field.options)

	def add_role_permissions_for_select_doctypes(self):
		for doctype in ["select_doctypes", "custom_select_doctypes"]:
			for row in self.get(doctype):
				docperm = add_role_permissions(row.document_type, self.role)
				update_custom_docperm(docperm, {"select": 1, "read": 0, "create": 0, "write": 0})

	def add_role_permissions_for_file(self):
		docperm = add_role_permissions("File", self.role)
		update_custom_docperm(docperm, {"read": 1, "create": 1, "write": 1})

	def remove_permission_for_deleted_doctypes(self):
		doctypes = [d.document_type for d in self.user_doctypes]

		# Do not remove the doc permission for the file doctype
		doctypes.append("File")

		for doctype in ["select_doctypes", "custom_select_doctypes"]:
			doctypes.extend(dt.document_type for dt in self.get(doctype))
		for perm in saashq.get_all(
			"Custom DocPerm", filters={"role": self.role, "parent": ["not in", doctypes]}
		):
			saashq.delete_doc("Custom DocPerm", perm.name)


def add_role_permissions(doctype, role):
	name = saashq.get_value("Custom DocPerm", dict(parent=doctype, role=role, permlevel=0))

	if not name:
		name = add_permission(doctype, role, 0)

	return name


def get_non_standard_user_types():
	user_types = saashq.get_all(
		"User Type",
		fields=["apply_user_permission_on", "name", "user_id_field"],
		filters={"is_standard": 0},
	)

	return {d.name: [d.apply_user_permission_on, d.user_id_field] for d in user_types}


@saashq.whitelist()
@saashq.validate_and_sanitize_search_inputs
def get_user_linked_doctypes(doctype, txt, searchfield, start, page_len, filters):
	modules = [d.get("module_name") for d in get_modules_from_app("saashq")]

	filters = [
		["DocField", "options", "=", "User"],
		["DocType", "is_submittable", "=", 0],
		["DocType", "issingle", "=", 0],
		["DocType", "module", "not in", modules],
		["DocType", "read_only", "=", 0],
		["DocType", "name", "like", f"%{txt}%"],
	]

	doctypes = saashq.get_all(
		"DocType",
		fields=["`tabDocType`.`name`"],
		filters=filters,
		order_by="`tabDocType`.`idx` desc",
		limit_start=start,
		limit_page_length=page_len,
		as_list=1,
	)

	custom_dt_filters = [
		["Custom Field", "dt", "like", f"%{txt}%"],
		["Custom Field", "options", "=", "User"],
		["Custom Field", "fieldtype", "=", "Link"],
	]

	custom_doctypes = saashq.get_all(
		"Custom Field", fields=["dt as name"], filters=custom_dt_filters, as_list=1
	)

	return doctypes + custom_doctypes


@saashq.whitelist()
def get_user_id(parent):
	data = (
		saashq.get_all(
			"DocField",
			fields=["label", "fieldname as value"],
			filters={"options": "User", "fieldtype": "Link", "parent": parent},
		)
		or []
	)

	data.extend(
		saashq.get_all(
			"Custom Field",
			fields=["label", "fieldname as value"],
			filters={"options": "User", "fieldtype": "Link", "dt": parent},
		)
	)

	return data


def user_linked_with_permission_on_doctype(doc, user):
	if not doc.apply_user_permission_on:
		return True

	if not doc.user_id_field:
		saashq.throw(_("User Id Field is mandatory in the user type {0}").format(saashq.bold(doc.name)))

	if saashq.db.get_value(doc.apply_user_permission_on, {doc.user_id_field: user}, "name"):
		return True
	else:
		label = saashq.get_meta(doc.apply_user_permission_on).get_field(doc.user_id_field).label

		saashq.msgprint(
			_(
				"To set the role {0} in the user {1}, kindly set the {2} field as {3} in one of the {4} record."
			).format(
				saashq.bold(doc.role),
				saashq.bold(user),
				saashq.bold(label),
				saashq.bold(user),
				saashq.bold(doc.apply_user_permission_on),
			)
		)

		return False


def apply_permissions_for_non_standard_user_type(doc, method=None):
	"""Create user permission for the non standard user type"""
	if not saashq.db.table_exists("User Type") or saashq.flags.in_migrate:
		return

	user_types = saashq.cache.get_value(
		"non_standard_user_types",
		get_non_standard_user_types,
	)

	if not user_types:
		return

	for user_type, data in user_types.items():
		if not doc.get(data[1]) or doc.doctype != data[0]:
			continue

		if saashq.get_cached_value("User", doc.get(data[1]), "user_type") != user_type:
			return

		if doc.get(data[1]) and (
			not doc._doc_before_save
			or doc.get(data[1]) != doc._doc_before_save.get(data[1])
			or not saashq.db.get_value(
				"User Permission", {"user": doc.get(data[1]), "allow": data[0], "for_value": doc.name}, "name"
			)
		):
			perm_data = saashq.db.get_value(
				"User Permission", {"allow": doc.doctype, "for_value": doc.name}, ["name", "user"]
			)

			if not perm_data:
				user_doc = saashq.get_cached_doc("User", doc.get(data[1]))
				user_doc.set_roles_and_modules_based_on_user_type()
				user_doc.update_children()
				add_user_permission(doc.doctype, doc.name, doc.get(data[1]))
			else:
				user_perm = saashq.get_doc("User Permission", perm_data[0])
				user_perm.user = doc.get(data[1])
				user_perm.save(ignore_permissions=True)
