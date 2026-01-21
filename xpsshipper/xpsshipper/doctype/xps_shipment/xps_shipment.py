# Copyright (c) 2026, Kemal Korucu and contributors
# For license information, please see license.txt

from pydoc import doc
import frappe
from frappe.model.document import Document
from frappe import _



class XPSShipment(Document):
    ignore_links_on_cancel = True
    ignore_links_on_delete = True

    def validate(self):
        self.validate_customer_delivery_notes()
        self.validate_duplicate_delivery_notes()
        self.sync_delivery_notes()
        self.validate_package_type()

    def on_update(self):
        self.sync_delivery_notes()

    def validate_package_type(self):
        if not self.shipping_service or not self.package_type:
            return

        # This returns a list of strings
        valid_types = frappe.get_all(
            "XPS Package Type",
            filters={"parent": self.shipping_service, "parenttype": "XPS Service"},
            pluck="package_type_code"
        )

        if self.package_type not in valid_types:
            frappe.throw(
                _("Package Type {0} is not valid for Shipping Service {1}").format(
                    frappe.bold(self.package_type),
                    frappe.bold(self.shipping_service)
                )
            )

    def before_submit(self):
        if not self.tracking_numbers:
            frappe.throw(
                _("At least one Tracking Number is required before submitting the XPS Shipment."),
                title=_("Missing Tracking Number")
            )

    # --------------------------------------------------
    # Validate Customer consistency of Delivery Notes
    # --------------------------------------------------
    def validate_customer_delivery_notes(self):
        if not self.customer:
            return

        for row in self.delivery_notes:
            if not row.delivery_note:
                continue

            dn_customer = frappe.db.get_value(
                "Delivery Note",
                row.delivery_note,
                "customer"
            )

            if dn_customer != self.customer:
                frappe.throw(
                    _("Delivery Note <b>{0}</b> belongs to Customer <b>{1}</b>, "
                    "but this XPS Shipment is for Customer <b>{2}</b>.")
                    .format(
                        row.delivery_note,
                        dn_customer or _("(None)"),
                        self.customer
                    ),
                    title=_("Customer Mismatch")
                )

    # --------------------------------------------------
    # Validate uniqueness of Delivery Notes
    # --------------------------------------------------
    def validate_duplicate_delivery_notes(self):
        seen = set()

        for row in self.delivery_notes:
            if not row.delivery_note:
                continue

            if row.delivery_note in seen:
                frappe.throw(
                    _("Delivery Note {0} is already added.")
                    .format(frappe.bold(row.delivery_note))
                )

            seen.add(row.delivery_note)

        for row in self.delivery_notes:
            if not row.delivery_note:
                continue

            existing = frappe.get_all(
                "XPS Shipment Delivery Note",
                filters={
                    "delivery_note": row.delivery_note,
                    "parent": ["!=", self.name],
                    "parenttype": "XPS Shipment",
                    "parentfield": "delivery_notes",
                },
                fields=["parent"],
                limit=1,
            )

            if existing:
                frappe.throw(
                    _("Delivery Note <b>{0}</b> is already linked to XPS Shipment <b>{1}</b>.")
                    .format(row.delivery_note, existing[0].parent),
                    title=_("Duplicate Delivery Note"),
                )

    # --------------------------------------------------
    # Sync Delivery Note ↔ XPS Shipment link
    # --------------------------------------------------
    def sync_delivery_notes(self):
        previous_dns = self.get_previous_delivery_notes()
        current_dns = {row.delivery_note for row in self.delivery_notes if row.delivery_note}

        # Newly added DNs
        added_dns = current_dns - previous_dns

        # Removed DNs
        removed_dns = previous_dns - current_dns

        # Set link for added DNs
        for dn in added_dns:
            self.update_delivery_note_link(dn, self.name)

        # Clear link for removed DNs
        for dn in removed_dns:
            self.update_delivery_note_link(dn, None)

    def get_previous_delivery_notes(self):
        if self.is_new():
            return set()

        previous = frappe.get_all(
            "XPS Shipment Delivery Note",
            filters={
                "parent": self.name,
                "parenttype": "XPS Shipment",
                "parentfield": "delivery_notes",
            },
            pluck="delivery_note",
        )

        return set(previous)

    def update_delivery_note_link(self, delivery_note, shipment_name):
        dn = None

        if shipment_name:
            # Only check when linking
            dn = frappe.db.get_value(
                "Delivery Note",
                delivery_note,
                "custom_xps_shipment"
            )

            if dn and dn != shipment_name:
                frappe.throw(
                    _("Delivery Note {0} is already linked to XPS Shipment {1}.")
                    .format(frappe.bold(delivery_note), frappe.bold(dn))
                )

        # Always update link via DB only
        frappe.db.set_value(
            "Delivery Note",
            delivery_note,
            "custom_xps_shipment",
            shipment_name,
            update_modified=False,
        )

    # --------------------------------------------------
    # Cancellation logic
    # --------------------------------------------------
    def before_cancel(self):
        pass

    def on_cancel(self):
        self.unlink_all_delivery_notes()
        self.clear_delivery_notes_table()

    def unlink_all_delivery_notes(self):
        """
        Remove XPS Shipment link from Delivery Notes
        WITHOUT loading the documents.
        """
        frappe.db.sql(
            """
            UPDATE `tabDelivery Note`
            SET custom_xps_shipment = NULL
            WHERE custom_xps_shipment = %s
            """,
            self.name,
        )

    def clear_delivery_notes_table(self):
        """
        Remove all Delivery Note rows from the delivery_notes child table
        when the XPS Shipment is cancelled.
        """
        self.set("delivery_notes", [])
######################################################################################################
def before_delete(doc, method):
    """
    Before deleting an XPS Shipment, unlink all Delivery Notes.
    Only Draft shipments are allowed.
    """
    if doc.docstatus != 0:
        frappe.throw(_("Only Draft XPS Shipments can be deleted."))

    frappe.db.sql(
        """
        UPDATE `tabDelivery Note`
        SET custom_xps_shipment = NULL
        WHERE custom_xps_shipment = %s
        """,
        doc.name,
    )

    # Clear child table
    doc.set("delivery_notes", [])
    doc.flags.ignore_mandatory = True
    doc.db_update()

######################################################################################################
@frappe.whitelist()
def get_package_type_options(service=None):
    """
    Returns a list of package_type_code strings for the selected shipping_service.
    """
    if not service:
        return []

    package_types = frappe.get_all(
        "XPS Package Type",
        filters={"parent": service, "parenttype": "XPS Service"},
        fields=["package_type_code"],  # <-- corrected
        order_by="idx"
    )

    return [pt["package_type_code"] for pt in package_types]

