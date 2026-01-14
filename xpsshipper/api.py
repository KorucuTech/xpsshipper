import xpsshipper.xps as xps
import requests
import frappe

def call_xps_api(name, payload=None,**params):

    try:
        settings = frappe.get_single("XPS Settings")

        if not settings  or not settings.api_key or not settings.customer_id or not settings.api_base_url:
            frappe.throw("XPS Settings incomplete. Please configure in XPS Settings.") 

        params.update({
            "api_base_url": (settings.get("api_base_url") or "").strip().rstrip("/"),
            "customer_id": (settings.get("customer_id") or "").strip(),
            "api_key": (settings.get_password("api_key", raise_exception=False) or "").strip(),
            "integration_id": (settings.get("integration_id") or "").strip(),
            "payload": payload if payload else {},
        })

        if name in xps.ECOMMERCE_API_ENDPOINTS and settings.enable_ecommerce_rest_api:
            endpoint = xps.build_endpoint(xps.ECOMMERCE_API_ENDPOINTS, name, **params)
        elif name in xps.CORE_API_ENDPOINTS and settings.enable_core_rest_api:
            endpoint = xps.build_endpoint(xps.CORE_API_ENDPOINTS, name, **params)
        else:
            frappe.throw(f"Unknown XPS API endpoint: {name} or the API is not enabled in XPS Settings.")

        method = endpoint.get("method")
        url = endpoint.get("url")

        headers = {
            "Authorization": f"RSIS {params.get('api_key')}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Make the HTTP request
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            headers=headers,
            timeout=30
        )

        # Raise error for bad responses
        response.raise_for_status()

        # Return JSON response, or empty dict if no content
        return response.json() if response.content else {}

    except requests.exceptions.RequestException as e:
        print(e.__str__())
        frappe.log_error(frappe.get_traceback(), f"XPS API request error ({name})")
        frappe.throw(f"XPS API request error: {str(e)}")
    except KeyError as e:
        print(e)
        frappe.log_error(frappe.get_traceback(), f"XPS API missing parameter ({name})")
        frappe.throw(f"Missing parameter for XPS API request: {str(e)}")
    except Exception as e:
        print(e)
        frappe.log_error(frappe.get_traceback(), f"XPS API unknown error ({name})")
        frappe.throw(f"XPS API call failed: {str(e)}")

######################################################################################################
@frappe.whitelist()
def check_xps_shipment_before_create(delivery_note):
    """
    Check if a Delivery Note already has XPS Shipments.
    Returns a warning if it does, so client can ask for confirmation.
    """
    try:
        dn = frappe.get_doc("Delivery Note", delivery_note)
    except frappe.DoesNotExistError:
        frappe.throw(f"Delivery Note {delivery_note} not found.")

    if dn.docstatus != 1:
        frappe.throw("Only submitted Delivery Notes can be sent to XPS Shipper.")

    # Check for existing XPS Shipments
    existing_shipments = frappe.get_all(
        "XPS Shipment Delivery Note",
        filters={"delivery_note": dn.name},
        fields=["parent"]
    )

    if existing_shipments:
        shipment_names = [s.parent for s in existing_shipments]
        return {
            "warning": True,
            "message": f"Delivery Note {dn.name} is already linked to XPS Shipment(s): {', '.join(shipment_names)}"
        }

    return {"warning": False}

######################################################################################################
@frappe.whitelist()
def create_xps_shipment_from_dn(delivery_note):
    dn = frappe.get_doc("Delivery Note", delivery_note)
    if not dn:
        frappe.throw("Delivery Note not found.")
    if dn.docstatus != 1:
        frappe.throw("Only submitted Delivery Notes can be sent to XPS Shipper.")

    # Check for existing shipments
    existing_shipments = frappe.get_all(
        "XPS Shipment Delivery Note",  # child table linking DN → XPS Shipment
        filters={"delivery_note": dn.name},
        fields=["parent"]
    )

    if existing_shipments:
        shipment_names = [s.parent for s in existing_shipments]
        frappe.msgprint(
            f"Warning: Delivery Note {dn.name} is already linked to XPS Shipment(s): {', '.join(shipment_names)}",
            alert=True
        )

    xps = frappe.new_doc("XPS Shipment")

    xps.customer = dn.customer
    xps.order_date =  frappe.utils.nowdate()
    xps.append("delivery_notes",{
        "delivery_note": dn.name,
        "value": dn.grand_total
    })

    if dn.dispatch_address_name:
        xps.sender_address_name = dn.dispatch_address_name
    else:
        xps.sender_address_name = dn.company_address

    if dn.shipping_address_name:
        xps.receiver_address_name = dn.shipping_address_name
    else:
        xps.receiver_address_name = dn.billing_address_name

    xps.insert()

    return xps.name