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
        {
            "label": "Sales Order",
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 140,
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "SO Date",
            "fieldname": "so_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": "Delivery Date",
            "fieldname": "delivery_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "PO Number",
            "fieldname": "po_no",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Picked %",
            "fieldname": "picked_percent",
            "fieldtype": "Percent",
            "width": 110,
        },
        {
            "label": "Pick Lists",
            "fieldname": "pick_lists",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Pick List Status",
            "fieldname": "pl_status",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": "Delivery Note",
            "fieldname": "delivery_note",
            "fieldtype": "Link",
            "options": "Delivery Note",
            "width": 140,
        },
        {
            "label": "DN Status",
            "fieldname": "dn_status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Sales Invoice",
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 140,
        },
        {
            "label": "SI Status",
            "fieldname": "si_status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "XPS Shipment",
            "fieldname": "xps_shipment",
            "fieldtype": "Link",
            "options": "XPS Shipment",
            "width": 140,
        },
        {
            "label": "Tracking Numbers",
            "fieldname": "tracking_numbers",
            "fieldtype": "Data",
            "width": 250,
        },
    ]


# ---------------------------
# DATA
# ---------------------------
def get_data(filters):
    if not filters or not filters.get("customer"):
        return []

    customer = filters.get("customer")

    rows = frappe.db.sql(
        """
        SELECT
            so.name AS sales_order,
            so.status AS so_status,
            so.transaction_date AS so_date,
            so.delivery_date AS delivery_date,
            so.po_no AS po_no,

            MAX(dn.name) AS delivery_note,
            MAX(dn.status) AS dn_status,

            MAX(si.name) AS sales_invoice,
            MAX(si.status) AS si_status,

            MAX(xs.name) AS xps_shipment

        FROM `tabSales Order` so

        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = so.name

        LEFT JOIN `tabDelivery Note` dn
            ON dn.name = dni.parent
            AND dn.docstatus = 1

        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.dn_detail = dni.name

        LEFT JOIN `tabSales Invoice` si
            ON si.name = sii.parent
            AND si.docstatus = 1

        LEFT JOIN `tabXPS Shipment` xs
            ON xs.name = dn.custom_xps_shipment

        WHERE
            so.customer = %(customer)s
            AND so.docstatus = 1

        GROUP BY
            so.name,
            so.status,
            so.transaction_date,
            so.delivery_date,
            so.po_no

        ORDER BY so.transaction_date DESC
        """,
        {"customer": customer},
        as_dict=True,
    )

    result = []

    for r in rows:

        so_name = r.sales_order

        # ---------------------------
        # SALES ORDER TOTAL QTY
        # ---------------------------
        so_qty = (
            frappe.db.sql(
                """
                SELECT SUM(qty)
                FROM `tabSales Order Item`
                WHERE parent = %s
                """,
                so_name,
            )[0][0]
            or 0
        )

        # ---------------------------
        # PICKED QTY
        # SUBMITTED PICK LISTS ONLY
        # ---------------------------
        picked_qty = (
            frappe.db.sql(
                """
                SELECT SUM(pli.qty)
                FROM `tabPick List Item` pli
                INNER JOIN `tabPick List` pl
                    ON pl.name = pli.parent
                WHERE
                    pl.docstatus = 1
                    AND pli.sales_order_item IN (
                        SELECT name
                        FROM `tabSales Order Item`
                        WHERE parent = %s
                    )
                """,
                so_name,
            )[0][0]
            or 0
        )

        picked_percent = (picked_qty / so_qty * 100) if so_qty else 0

        # ---------------------------
        # PICK LISTS
        # SUBMITTED ONLY
        # ---------------------------
        pl_data = frappe.db.sql(
            """
            SELECT
                pl.name,
                pl.status
            FROM `tabPick List` pl
            INNER JOIN `tabPick List Item` pli
                ON pli.parent = pl.name
            WHERE
                pl.docstatus = 1
                AND pli.sales_order_item IN (
                    SELECT name
                    FROM `tabSales Order Item`
                    WHERE parent = %s
                )
            GROUP BY pl.name, pl.status
            """,
            so_name,
        )

        pick_lists = ", ".join(d[0] for d in pl_data) if pl_data else None
        pl_status = ", ".join(d[1] for d in pl_data) if pl_data else None

        # ---------------------------
        # TRACKING NUMBERS
        # ---------------------------
        tracking_numbers = []

        if r.xps_shipment:
            tracking_numbers = frappe.get_all(
                "XPS Tracking Number",
                filters={"parent": r.xps_shipment},
                pluck="tracking_number",
            )

        tracking_str = ", ".join(tracking_numbers) if tracking_numbers else None

        # ---------------------------
        # CUSTOMER STATUS
        # ---------------------------
        if r.sales_invoice:
            status = "✅ Invoiced"

        elif r.delivery_note:
            if tracking_numbers:
                status = "🚚 In Transit"
            else:
                status = "🔵 Shipped (No Tracking Yet)"

        elif picked_percent > 0:
            status = "🟠 Picked"

        else:
            status = "🟡 Order Received"

        # ---------------------------
        # FINAL ROW
        # ---------------------------
        result.append(
            {
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
                "tracking_numbers": tracking_str,
            }
        )

    return result