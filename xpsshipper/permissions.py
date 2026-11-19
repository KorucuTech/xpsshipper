import frappe
from frappe import _
from frappe.desk.query_report import run as original_run

@frappe.whitelist()
def custom_query_report_run(report_name=None, filters=None, **kwargs):
    # Check if the user is "webuser" (case-insensitive)
    user = frappe.session.user or ""
    if "webuser" in user.lower().strip():
        # If they are trying to run the specific report, block it
        if report_name == "Order Tracking 3":
            frappe.throw(
                _("API access to the Order Tracking 3 report is temporarily disabled for this user."),
                frappe.PermissionError
            )
    
    # Otherwise, run the original report as normal
    return original_run(report_name=report_name, filters=filters, **kwargs)