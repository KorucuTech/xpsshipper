import frappe
import json
from frappe import _

def block_api_report_access():
    # Check if we are in an active HTTP request
    if not getattr(frappe.local, "request", None):
        return

    # Only target the specific report execution endpoint
    if frappe.local.request.path == "/api/method/frappe.desk.query_report.run":
        
        # Check if the user contains "webuser" (case-insensitive)
        user = frappe.session.user or ""
        if "webuser" in user.lower().strip():
            
            report_name = None
            
            # 1. Try to get the report name from standard form data
            if frappe.form_dict:
                report_name = frappe.form_dict.get("report_name")
            
            # 2. If not found, parse the raw JSON body (Frappe API often sends JSON)
            if not report_name and hasattr(frappe.local.request, "data"):
                try:
                    data = json.loads(frappe.local.request.data)
                    report_name = data.get("report_name")
                except Exception:
                    pass
            
            # 3. If the requested report is "Order Tracking 3", block it
            if report_name == "Order Tracking 3":
                frappe.throw(
                    _("API access to the Order Tracking 3 report is temporarily disabled for this user."),
                    frappe.PermissionError
                )