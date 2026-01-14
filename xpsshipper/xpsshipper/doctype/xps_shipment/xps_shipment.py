# Copyright (c) 2026, Kemal Korucu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class XPSShipment(Document):

	def validate(self):
		self.validate_duplicate_delivery_notes()


	def validate_duplicate_delivery_notes(self):
		seen = set()

		for row in self.delivery_notes:
			if not row.delivery_note:
				continue

			if row.delivery_note in seen:
				frappe.throw(
					_("Delivery Note {0} is already added.").format(
						frappe.bold(row.delivery_note)
					)
				)

			seen.add(row.delivery_note)
