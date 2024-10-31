# Copyright (c) 2020, Saashq Technologies and contributors
# License: MIT. See LICENSE

import saashq
from saashq import _
from saashq.model.document import Document
from saashq.model.naming import parse_naming_series
from saashq.utils.data import evaluate_filters


class DocumentNamingRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from saashq.core.doctype.document_naming_rule_condition.document_naming_rule_condition import (
			DocumentNamingRuleCondition,
		)
		from saashq.types import DF

		conditions: DF.Table[DocumentNamingRuleCondition]
		counter: DF.Int
		disabled: DF.Check
		document_type: DF.Link
		prefix: DF.Data
		prefix_digits: DF.Int
		priority: DF.Int
	# end: auto-generated types

	def validate(self):
		self.validate_fields_in_conditions()

	def clear_doctype_map(self):
		saashq.cache_manager.clear_doctype_map(self.doctype, self.document_type)

	def on_update(self):
		self.clear_doctype_map()

	def on_trash(self):
		self.clear_doctype_map()

	def validate_fields_in_conditions(self):
		if self.has_value_changed("document_type"):
			docfields = [x.fieldname for x in saashq.get_meta(self.document_type).fields]
			for condition in self.conditions:
				if condition.field not in docfields:
					saashq.throw(
						_("{0} is not a field of doctype {1}").format(
							saashq.bold(condition.field), saashq.bold(self.document_type)
						)
					)

	def apply(self, doc):
		"""
		Apply naming rules for the given document. Will set `name` if the rule is matched.
		"""
		if self.conditions:
			if not evaluate_filters(
				doc, [(self.document_type, d.field, d.condition, d.value) for d in self.conditions]
			):
				return

		counter = saashq.db.get_value(self.doctype, self.name, "counter", for_update=True) or 0
		naming_series = parse_naming_series(self.prefix, doc=doc)

		doc.name = naming_series + ("%0" + str(self.prefix_digits) + "d") % (counter + 1)
		saashq.db.set_value(self.doctype, self.name, "counter", counter + 1)
