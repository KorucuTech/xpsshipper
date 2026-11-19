import frappe
from frappe import _

def report_has_permission(doc, ptype, user):
    BLOCKED_REPORT = "Order Tracking 3"
    
    if doc.name == BLOCKED_REPORT:
        # Check if this is an API call
        if frappe.local.request:
            # Check if the user email contains "webuser" (case-insensitive)
            if user and "webuser" in user.lower().strip():
                frappe.throw(
                    _("API access to the Order Tracking 3 report is temporarily disabled for this user."), 
                    frappe.PermissionError
                )
                return False

    # Allow all other users and standard Desk UI requests
    return None