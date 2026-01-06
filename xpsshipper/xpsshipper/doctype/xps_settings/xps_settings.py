# Copyright (c) 2026, Kemal Korucu and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document


class XPSSettings(Document):
    pass


@frappe.whitelist()
def test_api_access(docname):
    """
    Test the XPS Shipper API key by making a simple authenticated request.
    This assumes you have created a REST API Integration in your XPS Webship account
    and have an Integration ID + API Key/Secret.
    """
    doc = frappe.get_doc("XPS Settings", docname)
    
    api_key = (doc.get_password("api_key", raise_exception=False) or "").strip()
    customer_id = (doc.get("customer_id") or "").strip()
    api_base_url = (doc.get("api_base_url") or "").strip().rstrip("/")
    
    if not api_key:
        frappe.throw(_("Please enter an API Key first."))

    if not customer_id:
        frappe.throw(_("Please enter a Customer ID first."))

    if not api_base_url:
        frappe.throw(_("Please enter an API Base URL first."))

    url = f"{api_base_url}/customers/{customer_id}/services"

    headers = {
        "Authorization": f"RSIS {api_key}",
		"Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code in (200, 201):
            # Success → key is valid
            data = response.json()
            msg = _("API connection successful!<br>Your information is valid.")
            if isinstance(data, list) and len(data) > 0:
                msg += _("<br>Found {} services/carriers.".format(len(data)))

            frappe.msgprint(
                title=_("Success"),
                msg=msg,
                indicator="green"
            )

        else:
            # Error from API
            error_text = response.text[:400] if response.text else "No details"
            frappe.msgprint(
                title=_("API Test Failed"),
                msg=_(
                    f"Status: {response.status_code}<br>"
                    f"Response: {error_text}"
                ),
                indicator="red"
            )

    except requests.exceptions.Timeout:
        frappe.msgprint(
            title=_("Timeout"),
            msg=_("Request timed out. Check your internet or the API URL."),
            indicator="orange"
        )
    except requests.exceptions.ConnectionError:
        frappe.msgprint(
            title=_("Connection Error"),
            msg=_("Could not reach XPS Shipper API. Check URL/network."),
            indicator="orange"
        )
    except Exception as e:
        frappe.msgprint(
            title=_("Error"),
            msg=str(e),
            indicator="red"
        )