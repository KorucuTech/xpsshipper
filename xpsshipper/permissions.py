import frappe
from frappe import _

def report_has_permission(doc, ptype, user):
    # The exact name of the report
    BLOCKED_REPORT = "Order Tracking 3"
    
    # The specific user to block
    BLOCKED_USER = "webuser"

    if doc.name == BLOCKED_REPORT:
        # Block the specific user ONLY if they are making an API call
        if user == BLOCKED_USER and frappe.local.request:
            frappe.throw(
                _("API access to the Order Tracking 3 report is temporarily disabled for this user."), 
                frappe.PermissionError
            )
            return False

    # Allow all other users and standard Desk UI requests
    return None