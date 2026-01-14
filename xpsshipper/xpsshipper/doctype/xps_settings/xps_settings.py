# Copyright (c) 2026, Kemal Korucu and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document
from xpsshipper import api 



class XPSSettings(Document):
    pass


@frappe.whitelist()
def test_api_access(docname):
   
    try:
        api.call_xps_api("list_services", payload={})

        frappe.msgprint(
            title=_("Success"),
            msg=_("Successfully connected to XPS Shipper API."),
            indicator="green"
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