# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE


class DocStatus(int):
	def is_draft(self):
		return self == self.draft()

	def is_submitted(self):
		return self == self.submitted()

	def is_cancelled(self):
		return self == self.cancelled()

	@classmethod
	def draft(cls):
		return cls(0)

	@classmethod
	def submitted(cls):
		return cls(1)

	@classmethod
	def cancelled(cls):
		return cls(2)
