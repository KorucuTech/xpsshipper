import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Sales Order ID",
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 180
        },
        {
            "label": "SO Date",
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": "SO Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150
        }
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("customer"):
        conditions.append("customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("so_date_from"):
        conditions.append("transaction_date >= %(so_date_from)s")
        values["so_date_from"] = filters.get("so_date_from")

    if filters.get("so_date_thru"):
        conditions.append("transaction_date <= %(so_date_thru)s")
        values["so_date_thru"] = filters.get("so_date_thru")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            name AS sales_order,
            transaction_date,
            status
        FROM `tabSales Order`
        {where_clause}
        ORDER BY transaction_date DESC, name DESC
        """,
        values,
        as_dict=True,
    )