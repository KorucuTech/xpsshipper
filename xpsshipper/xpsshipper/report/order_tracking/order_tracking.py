import frappe
from frappe import _
import itertools

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 160},
        {"label": "SO Status", "fieldname": "so_status", "fieldtype": "Data", "width": 110},
        {"label": "SO Date", "fieldname": "so_date", "fieldtype": "Date", "width": 100},
        {"label": "Delivery Date (SO)", "fieldname": "delivery_date", "fieldtype": "Date", "width": 120},
        {"label": "Pick List", "fieldname": "pick_list", "fieldtype": "Link", "options": "Pick List", "width": 150},
        {"label": "PL Status", "fieldname": "pick_list_status", "fieldtype": "Data", "width": 110},
        {"label": "Delivery Note", "fieldname": "delivery_note", "fieldtype": "Link", "options": "Delivery Note", "width": 150},
        {"label": "DN Status", "fieldname": "delivery_note_status", "fieldtype": "Data", "width": 110},
        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
        {"label": "SI Status", "fieldname": "sales_invoice_status", "fieldtype": "Data", "width": 110},
        {"label": "XPS Shipment", "fieldname": "xps_shipment", "fieldtype": "Link", "options": "XPS Shipment", "width": 150},
        {"label": "XPS Status", "fieldname": "xps_status", "fieldtype": "Data", "width": 110},
        {"label": "Tracking Number", "fieldname": "tracking_number", "fieldtype": "Data", "width": 150},
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
        fields=["name", "status", "transaction_date as so_date", "delivery_date"],
        order_by="creation asc"
    )
    if not so_list:
        return []

    so_names = [so.name for so in so_list]
    so_map = {so.name: so for so in so_list}

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
        dn_xps_map = {}
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
    if si_names:
        si_docs = frappe.get_all(
            "Sales Invoice",
            filters={"name": ["in", si_names]},
            fields=["name", "status"]
        )
        si_status_map = {si.name: si.status for si in si_docs}

    # ───────────────────────────────────────────────
    # XPS Shipments
    xps_names = list({xps for xsps in dn_xps_map.values() for xps in xsps})
    xps_status_map = {}
    xps_tracking_map = {}
    if xps_names:
        xps_docs = frappe.get_all(
            "XPS Shipment",
            filters={"name": ["in", xps_names]},
            fields=["name", "docstatus"]
        )
        status_dict = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
        xps_status_map = {xps.name: status_dict.get(xps.docstatus, "") for xps in xps_docs}

        # Fetch first tracking number per XPS Shipment
        tracking_list = frappe.get_all(
            "XPS Tracking Number",
            filters={"parent": ["in", xps_names]},
            fields=["parent", "tracking_number"],
            order_by="idx asc"
        )
        for xps_name in xps_names:
            # take first tracking number for this XPS
            tracking_numbers = [t.tracking_number for t in tracking_list if t.parent == xps_name]
            xps_tracking_map[xps_name] = tracking_numbers[0] if tracking_numbers else None

    # ───────────────────────────────────────────────
    # Build rows using cartesian product
    rows = []
    for so in so_list:
        pick_lists = list(so_pl_map.get(so.name, [None])) or [None]
        delivery_notes = list(so_dn_map.get(so.name, [None])) or [None]
        sales_invoices = list(so_si_map.get(so.name, [None])) or [None]

        # For each combination of PL, DN, SI
        for pl, dn, si in itertools.product(pick_lists, delivery_notes, sales_invoices):
            xps_set = dn_xps_map.get(dn, [None]) if dn else [None]
            for xps in xps_set:
                rows.append({
                    "sales_order": so.name,
                    "so_status": so.status,
                    "so_date": so.so_date,
                    "delivery_date": so.delivery_date,
                    "pick_list": pl,
                    "pick_list_status": pl_status_map.get(pl),
                    "delivery_note": dn,
                    "delivery_note_status": dn_status_map.get(dn),
                    "sales_invoice": si,
                    "sales_invoice_status": si_status_map.get(si),
                    "xps_shipment": xps,
                    "xps_status": xps_status_map.get(xps),
                    "tracking_number": xps_tracking_map.get(xps),
                })

    return rows
