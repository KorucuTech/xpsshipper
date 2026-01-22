import frappe
from frappe import _
import itertools


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 160, "align": "left"},
        {"label": "SO Status", "fieldname": "so_status", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "SO Date", "fieldname": "so_date", "fieldtype": "Date", "width": 100, "align": "left"},
        {"label": "Delivery Date (SO)", "fieldname": "delivery_date", "fieldtype": "Date", "width": 120, "align": "left"},
        {"label": "PO Number", "fieldname": "po_no", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "Pick List", "fieldname": "pick_list", "fieldtype": "Link", "options": "Pick List", "width": 150, "align": "left"},
        {"label": "PL Status", "fieldname": "pick_list_status", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "Delivery Note", "fieldname": "delivery_note", "fieldtype": "Link", "options": "Delivery Note", "width": 150, "align": "left"},
        {"label": "DN Status", "fieldname": "delivery_note_status", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150, "align": "left"},
        {"label": "SI Status", "fieldname": "sales_invoice_status", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "SI Date", "fieldname": "sales_invoice_date", "fieldtype": "Date", "width": 110, "align": "left"},
        {"label": "XPS Shipment", "fieldname": "xps_shipment", "fieldtype": "Link", "options": "XPS Shipment", "width": 150, "align": "left"},
        {"label": "XPS Status", "fieldname": "xps_status", "fieldtype": "Data", "width": 110, "align": "left"},
        {"label": "XPS Date", "fieldname": "xps_date", "fieldtype": "Date", "width": 110, "align": "left"},
        {"label": "Tracking Number", "fieldname": "tracking_number", "fieldtype": "Data", "width": 150, "align": "left"},
    ]



def get_data(filters):
    filters = filters or {}
    customer = filters.get("customer")
    if not customer:
        return []

    # ───────────────────────────────────────────────
    # Sales Orders
    so_list = frappe.get_all(
        "Sales Order",
        filters={"customer": customer, "docstatus": ["<", 2]},
        fields=["name", "status", "transaction_date as so_date", "delivery_date", "po_no"],
        order_by="creation asc"
    )
    if not so_list:
        return []

    so_names = [so.name for so in so_list]

    # ───────────────────────────────────────────────
    # Pick Lists
    pli_list = frappe.get_all(
        "Pick List Item",
        filters={"sales_order": ["in", so_names]},
        fields=["parent as pick_list", "sales_order"]
    )
    so_pl_map = {}
    for d in pli_list:
        so_pl_map.setdefault(d.sales_order, set()).add(d.pick_list)

    pl_names = list({pl for pls in so_pl_map.values() for pl in pls})
    pl_status_map = {}
    if pl_names:
        pl_docs = frappe.get_all(
            "Pick List",
            filters={"name": ["in", pl_names]},
            fields=["name", "status"]
        )
        pl_status_map = {pl.name: pl.status for pl in pl_docs}

    # ───────────────────────────────────────────────
    # Delivery Notes
    dni_list = frappe.get_all(
        "Delivery Note Item",
        filters={"against_sales_order": ["in", so_names], "docstatus": 1},
        fields=["parent as delivery_note", "against_sales_order as sales_order"]
    )
    so_dn_map = {}
    for d in dni_list:
        so_dn_map.setdefault(d.sales_order, set()).add(d.delivery_note)

    dn_names = list({dn for dns in so_dn_map.values() for dn in dns})
    dn_status_map = {}
    dn_xps_map = {}
    if dn_names:
        dn_docs = frappe.get_all(
            "Delivery Note",
            filters={"name": ["in", dn_names]},
            fields=["name", "status", "custom_xps_shipment"]
        )
        dn_status_map = {dn.name: dn.status for dn in dn_docs}
        for dn in dn_docs:
            if dn.custom_xps_shipment:
                dn_xps_map.setdefault(dn.name, set()).add(dn.custom_xps_shipment)

    # ───────────────────────────────────────────────
    # Sales Invoices
    sii_list = frappe.get_all(
        "Sales Invoice Item",
        filters={"sales_order": ["in", so_names], "docstatus": 1},
        fields=["parent as sales_invoice", "sales_order"]
    )
    so_si_map = {}
    for d in sii_list:
        so_si_map.setdefault(d.sales_order, set()).add(d.sales_invoice)

    si_names = list({si for sis in so_si_map.values() for si in sis})
    si_status_map = {}
    si_posting_date_map = {}
    if si_names:
        si_docs = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", si_names]},
            fields=["name", "status", "posting_date"]
        )
        si_status_map = {si.name: si.status for si in si_docs}
        si_posting_date_map = {si.name: si.posting_date for si in si_docs}

    # ───────────────────────────────────────────────
    # XPS Shipments
    xps_names = list({xps for xsps in dn_xps_map.values() for xps in xsps})
    xps_status_map = {}
    xps_date_map = {}
    xps_tracking_map = {}

    if xps_names:
        xps_docs = frappe.get_all(
            "XPS Shipment",
            filters={"name": ["in", xps_names]},
            fields=["name", "docstatus", "order_date"]
        )

        status_dict = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
        xps_status_map = {xps.name: status_dict.get(xps.docstatus, "") for xps in xps_docs}
        xps_date_map = {xps.name: xps.order_date for xps in xps_docs}

        tracking_list = frappe.get_all(
            "XPS Tracking Number",
            filters={"parent": ["in", xps_names]},
            fields=["parent", "tracking_number"],
            order_by="idx asc"
        )

        for xps_name in xps_names:
            rows = [t for t in tracking_list if t.parent == xps_name]
            xps_tracking_map[xps_name] = rows[0].tracking_number if rows else None

    # ───────────────────────────────────────────────
    # Build rows (cartesian product)
    rows = []
    for so in so_list:
        pick_lists = list(so_pl_map.get(so.name, [None])) or [None]
        delivery_notes = list(so_dn_map.get(so.name, [None])) or [None]
        sales_invoices = list(so_si_map.get(so.name, [None])) or [None]

        for pl, dn, si in itertools.product(pick_lists, delivery_notes, sales_invoices):
            xps_set = dn_xps_map.get(dn, [None]) if dn else [None]
            for xps in xps_set:
                rows.append({
                    "sales_order": so.name,
                    "so_status": so.status,
                    "so_date": so.so_date,
                    "delivery_date": so.delivery_date,
                    "po_no": so.po_no,
                    "pick_list": pl,
                    "pick_list_status": pl_status_map.get(pl),
                    "delivery_note": dn,
                    "delivery_note_status": dn_status_map.get(dn),
                    "sales_invoice": si,
                    "sales_invoice_status": si_status_map.get(si),
                    "sales_invoice_date": si_posting_date_map.get(si),
                    "xps_shipment": xps,
                    "xps_status": xps_status_map.get(xps),
                    "xps_date": xps_date_map.get(xps),
                    "tracking_number": xps_tracking_map.get(xps),
                })

    return rows
