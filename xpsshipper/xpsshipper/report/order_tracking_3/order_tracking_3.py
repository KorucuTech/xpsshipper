import frappe


def execute(filters=None):
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
            "label": "Invoices",
            "fieldname": "invoices",
            "fieldtype": "Data",
            "width": 250,
            "align": "left"
        }
    ]


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

    # If no statuses are selected, return no rows.
    if not selected_docstatus:
        return []

    conditions.append(f"so.docstatus IN ({','.join(selected_docstatus)})")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            so.customer,
            so.name AS sales_order,
            so.transaction_date,
            so.per_delivered,
            COALESCE(
                GROUP_CONCAT(
                    DISTINCT CASE
                        WHEN si.name IS NOT NULL THEN si.name
                    END
                    ORDER BY si.name
                    SEPARATOR ', '
                ),
                ''
            ) AS invoices,
            so.status
        FROM `tabSales Order` so
        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.sales_order = so.name
        LEFT JOIN `tabSales Invoice` si
            ON si.name = sii.parent
           AND si.docstatus = 1
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
