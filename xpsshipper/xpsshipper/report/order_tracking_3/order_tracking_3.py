import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = filters or {}

    if not filters.get("so_date_from"):
        filters["so_date_from"] = frappe.utils.add_days(
            frappe.utils.today(), -90
        )

    if not filters.get("so_date_thru"):
        filters["so_date_thru"] = frappe.utils.today()


    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Customer",
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180,
        },
        {
            "label": "Sales Order ID",
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 200
        },
        {
            "label": "Customer PO",
            "fieldname": "customer_po",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "SO Date",
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "% Delivered",
            "fieldname": "per_delivered",
            "fieldtype": "Percent",
            "width": 110,
        },
        {
            "label": "SO Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": "Order Status",
            "fieldname": "order_status",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Invoices",
            "fieldname": "invoices",
            "fieldtype": "Data",
            "width": 250,
            "align": "left"
        },
        {
            "label": "Tracking Numbers",
            "fieldname": "tracking_numbers",
            "fieldtype": "Data",
            "width": 750,
            "align": "left",
        },
    ]


def get_order_status(so_status, per_delivered):
    """
    Calculates the Order Status based on the provided matrix.
    """
    per_delivered = flt(per_delivered)

    # Draft and On Hold statuses
    if so_status == "Draft":
        return "Draft"
    if so_status == "On Hold":
        return "On Hold"
    
    # To Pay status (remains same regardless of delivery)
    if so_status == "To Pay":
        return "To Pay"
    
    # To Deliver and Bill / To Bill / To Deliver statuses
    if so_status in ["To Deliver and Bill", "To Bill", "To Deliver"]:
        if per_delivered == 0:
            return "In Progress"
        elif 1 <= per_delivered < 100:
            return "Partially Completed"
        elif per_delivered >= 100:
            return "Completed"
            
    # Completed status
    if so_status == "Completed":
        return "Completed"
    
    # Cancelled and Closed statuses
    if so_status in ["Cancelled", "Closed"]:
        if per_delivered == 0:
            return "Cancelled"
        elif 1 <= per_delivered < 100:
            return "Completed w/ Return(s)"
        elif per_delivered >= 100:
            # Based on the image, 100% delivered for Cancelled/Closed is empty/greyed out.
            # Returning None will leave the cell blank in the report.
            return None 
            
    # Fallback for any unmapped statuses
    return None


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("customer"):
        conditions.append("so.customer = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("so_date_from"):
        conditions.append("so.transaction_date >= %(so_date_from)s")
        values["so_date_from"] = filters["so_date_from"]

    if filters.get("so_date_thru"):
        conditions.append("so.transaction_date <= %(so_date_thru)s")
        values["so_date_thru"] = filters["so_date_thru"]

    selected_docstatus = []

    if filters.get("include_draft"):
        selected_docstatus.append("0")

    if filters.get("include_submitted"):
        selected_docstatus.append("1")

    if filters.get("include_canceled"):
        selected_docstatus.append("2")

    if not selected_docstatus:
        return []

    conditions.append(
        f"so.docstatus IN ({','.join(selected_docstatus)})"
    )

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    data = frappe.db.sql(
        f"""
        SELECT
            so.customer,
            so.name AS sales_order,
            so.po_no AS customer_po,
            so.transaction_date,
            so.per_delivered,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT si.name
                    ORDER BY si.name
                    SEPARATOR ', '
                ),
                ''
            ) AS invoices,

            COALESCE(
                GROUP_CONCAT(
                    DISTINCT xtn.tracking_number
                    ORDER BY xtn.tracking_number
                    SEPARATOR ', '
                ),
                ''
            ) AS tracking_numbers,

            so.status

        FROM `tabSales Order` so

        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.sales_order = so.name

        LEFT JOIN `tabSales Invoice` si
            ON si.name = sii.parent
            AND si.docstatus = 1


        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = so.name

        LEFT JOIN `tabDelivery Note` dn
            ON dn.name = dni.parent
            AND dn.docstatus = 1

        LEFT JOIN `tabXPS Shipment` xs
            ON xs.name = dn.custom_xps_shipment

        LEFT JOIN `tabXPS Tracking Number` xtn
            ON xtn.parent = xs.name
            AND xtn.parenttype = 'XPS Shipment'
            AND xtn.parentfield = 'tracking_numbers'

        {where_clause}

        GROUP BY
            so.name,
            so.customer,
            so.transaction_date,
            so.per_delivered,
            so.status

        ORDER BY
            so.customer,
            so.transaction_date DESC,
            so.name DESC
        """,
        values,
        as_dict=True,
    )

    # Apply the calculated Order Status logic to each row
    for row in data:
        row["order_status"] = get_order_status(row.get("status"), row.get("per_delivered"))

    return data