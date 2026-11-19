import frappe
from frappe import _

def report_has_permission(doc, ptype, user):
    BLOCKED_REPORT = "Order Tracking 3"
    
    # Hardcode the exact email address here
    BLOCKED_USER = "webuser@eurotard.com"

    if doc.name == BLOCKED_REPORT:
        # Block the user ONLY if they are making an API call
        if user == BLOCKED_USER and frappe.local.request:
            frappe.throw(
                _("API access to the Order Tracking 3 report is temporarily disabled for this user."), 
                frappe.PermissionError
            )
            return False

    return None