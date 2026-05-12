import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


# ---------------------------
# COLUMNS
# ---------------------------
def get_columns():
    return [
        {"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 140},

        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 180},

        {"label": "SO Date", "fieldname": "so_date", "fieldtype": "Date", "width": 100},
        {"label": "Delivery Date", "fieldname": "delivery_date", "fieldtype": "Date", "width": 120},
        {"label": "PO Number", "fieldname": "po_no", "fieldtype": "Data", "width": 120},

        {"label": "Picked %", "fieldname": "picked_percent", "fieldtype": "Percent", "width": 110},

        {"label": "Pick Lists", "fieldname": "pick_lists", "fieldtype": "Data", "width": 200},
        {"label": "Pick List Status", "fieldname": "pl_status", "fieldtype": "Data", "width": 140},

        {"label": "Delivery Note", "fieldname": "delivery_note", "fieldtype": "Link", "options": "Delivery Note", "width": 140},
        {"label": "DN Status", "fieldname": "dn_status", "fieldtype": "Data", "width": 120},

        {"label": "Sales Invoice", "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 140},
        {"label": "SI Status", "fieldname": "si_status", "fieldtype": "Data", "width": 120},

        {"label": "XPS Shipment", "fieldname": "xps_shipment", "fieldtype": "Link", "options": "XPS Shipment", "width": 140},

        {"label": "Tracking Numbers", "fieldname": "tracking_numbers", "fieldtype": "Data", "width": 250},
    ]


# ---------------------------
# DATA
# ---------------------------
def get_data(filters):
    if not filters or not filters.get("customer"):
        return []

    customer = filters.get("customer")

    rows = frappe.db.sql("""
        SELECT
            so.name AS sales_order,
            so.status AS so_status,
            so.transaction_date AS so_date,
            so.delivery_date AS delivery_date,
            so.po_no AS po_no,

            dn.name AS delivery_note,
            dn.status AS dn_status,

            si.name AS sales_invoice,
            si.status AS si_status,

            xs.name AS xps_shipment,

            so.name AS so_ref

        FROM `tabSales Order` so

        -- DN (truth layer)
        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = so.name

        LEFT JOIN `tabDelivery Note` dn
            ON dn.name = dni.parent
            AND dn.docstatus = 1

        -- Invoice (financial truth)
        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.dn_detail = dni.name

        LEFT JOIN `tabSales Invoice` si
            ON si.name = sii.parent
            AND si.docstatus = 1

        -- Shipment
        LEFT JOIN `tabXPS Shipment` xs
            ON xs.name = dn.custom_xps_shipment

        WHERE
            so.customer = %(customer)s

        GROUP BY so.name

        ORDER BY so.transaction_date DESC
    """, {"customer": customer}, as_dict=True)

    result = []

    # ---------------------------
    # ENRICH PER SALES ORDER
    # ---------------------------
    for r in rows:

        so = frappe.get_doc("Sales Order", r.sales_order)

        # ---------------------------
        # PICKED % (SOI vs PLI)
        # ---------------------------
        so_items = frappe.db.sql("""
            SELECT SUM(qty) as total_qty
            FROM `tabSales Order Item`
            WHERE parent = %s
        """, so.name)[0][0] or 0

        picked_qty = frappe.db.sql("""
            SELECT SUM(pli.qty)
            FROM `tabPick List Item` pli
            WHERE pli.sales_order_item IN (
                SELECT name FROM `tabSales Order Item` WHERE parent = %s
            )
        """, so.name)[0][0] or 0

        picked_percent = (picked_qty / so_items * 100) if so_items else 0

        # ---------------------------
        # PICK LISTS + STATUS
        # ---------------------------
        pl_data = frappe.db.sql("""
            SELECT pl.name, pl.status
            FROM `tabPick List` pl
            INNER JOIN `tabPick List Item` pli ON pli.parent = pl.name
            WHERE pli.sales_order_item IN (
                SELECT name FROM `tabSales Order Item` WHERE parent = %s
            )
            GROUP BY pl.name
        """, so.name)

        pick_lists = ", ".join([f"{d[0]}" for d in pl_data]) if pl_data else None
        pl_status = ", ".join([f"{d[1]}" for d in pl_data]) if pl_data else None

        # ---------------------------
        # TRACKING NUMBERS (MULTI BOX)
        # ---------------------------
        tracking_numbers = []

        if r.xps_shipment:
            tracking_numbers = frappe.get_all(
                "XPS Tracking Number",
                filters={"parent": r.xps_shipment},
                pluck="tracking_number"
            )

        tracking_str = ", ".join(tracking_numbers) if tracking_numbers else None

        # ---------------------------
        # CUSTOMER-FACING STATUS
        # ---------------------------
        if r.delivery_note:
            if tracking_numbers:
                status = "🚚 In Transit"
            else:
                status = "🔵 Shipped (No Tracking Yet)"
        else:
            if picked_percent > 0:
                status = "🟠 Picked"
            else:
                status = "🟡 Order Received"

        if r.sales_invoice:
            status = "✅ Invoiced"

        # ---------------------------
        # FINAL ROW
        # ---------------------------
        result.append({
            "sales_order": r.sales_order,
            "status": status,

            "so_date": r.so_date,
            "delivery_date": r.delivery_date,
            "po_no": r.po_no,

            "picked_percent": round(picked_percent, 2),

            "pick_lists": pick_lists,
            "pl_status": pl_status,

            "delivery_note": r.delivery_note,
            "dn_status": r.dn_status,

            "sales_invoice": r.sales_invoice,
            "si_status": r.si_status,

            "xps_shipment": r.xps_shipment,

            "tracking_numbers": tracking_str
        })

    return result