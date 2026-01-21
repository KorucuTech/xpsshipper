import frappe
from werkzeug.wrappers import Response
import json
from frappe import _
from frappe.utils import getdate, nowdate
from datetime import datetime, timezone


##################################################################################################
@frappe.whitelist(allow_guest=True)
def rest_api_update_order():
    # Check if REST API integration is enabled
    enabled = frappe.db.get_single_value("XPS Settings", "enable_rest_api")
    if not enabled:
        frappe.throw("XPS Shipper REST API is not enabled.", exc=frappe.PermissionError)

    # Verify secret
    received_secret = frappe.request.headers.get("x-rsis-key")
    expected_secret = frappe.db.get_single_value("XPS Settings", "rest_api_secret_key")
    if not expected_secret or received_secret != expected_secret:
        frappe.throw("Invalid webhook secret", exc=frappe.AuthenticationError)

    payload = frappe.request.get_json()
    frappe.log_error(title="XPS Update Order Webhook", message=str(payload))  # Debug log

    # TODO: Parse payload → update Delivery Note/Sales Order with tracking, status, label PDF URL
    # Example keys (from XPS docs): shipment_id, tracking_number, status, label_url, etc.

    data = {"status": "received"}

    # Return raw JSON directly
    return Response(
        json.dumps(data, ensure_ascii=False, indent=None),  
        mimetype='application/json'
    )

##################################################################################################
@frappe.whitelist(allow_guest=True,methods=["GET"])
def list_order():
    # Check if WEBHOOK integration is enabled
    enabled = frappe.db.get_single_value("XPS Settings", "enable_webhook")
    if not enabled:
        frappe.throw("XPS Shipper WEBHOOK is not enabled.", exc=frappe.PermissionError)

    # Verify secret
    received_secret = frappe.request.headers.get("x-rsis-key")
    expected_secret = frappe.db.get_single_value("XPS Settings", "webhook_secret_key")
    if not expected_secret or received_secret != expected_secret:
        frappe.throw("Invalid webhook secret", exc=frappe.AuthenticationError)

  # Fetch submitted Shipments (ready/shipped)
    shipments = frappe.get_all(
        "XPS Shipment",
        filters={
            "docstatus": 0,  # Draft only
            # Optional filters to narrow down (e.g., recent, pending carrier pickup, etc.)
            # "status": ["in", ["Open", "Ready to Ship", "Shipped"]],  # if you use status field
            # "shipment_date": [">=", "2025-12-01"]  # example: recent ones
        },
        fields=[
            "name",
            "order_date",
            "customer",
            "sender_address_name",
            "receiver_address_name",
            "shipping_service"
        ],
        order_by="creation desc",       # Newest first
        limit=50                        # Safety limit; add pagination later if needed
    )

    orders = []

    # Enrich each Shipment with linked Delivery Notes (child table)
    for shipment in shipments:
        if not shipment.sender_address_name or not shipment.receiver_address_name:
            continue  # Skip if addresses are missing

        pickup_address = frappe.db.get_value(
                    "Address",
                    shipment.sender_address_name,
                    [
                        "address_title",
                        "address_line1",
                        "address_line2",
                        "city",
                        "state",
                        "country",
                        "pincode",   # zip
                        "phone"
                    ],
                    as_dict=True
                ) or {}
        pickup_country_code = frappe.db.get_value("Country", pickup_address.country,"code") if pickup_address.country else None
        #pickup_contact = frappe.db.get_value("Contact",shipment.pickup_contact_name,["full_name","phone"],as_dict=True) or {}
    

        delivery_address = frappe.db.get_value(
                    "Address",
                    shipment.receiver_address_name,
                    [
                        "address_title",
                        "address_line1",
                        "address_line2",
                        "city",
                        "state",
                        "country",
                        "pincode",   # zip
                        "phone"
                    ],
                    as_dict=True
                ) or {}

        delivery_country_code = frappe.db.get_value("Country", delivery_address.country,"code") if delivery_address.country else None
        #delivery_contact = frappe.db.get_value("Contact",shipment.delivery_contact_name,["full_name","phone"],as_dict=True) or {}
        
     
        order_date = getdate(shipment.order_date) if shipment.order_date else getdate(nowdate())
        # Convert to UTC timestamp string
        local_dt = datetime.combine(order_date, datetime.min.time())
        utc_dt = local_dt.replace(tzinfo=timezone.utc)
        utc_timestamp = frappe.utils.get_datetime(utc_dt).timestamp()

        delivery_notes = frappe.get_all(
            "XPS Shipment Delivery Note",
            filters={"parent": shipment.name},
            fields=["delivery_note", "value"]
        )

        packages = []
        for parcel in frappe.get_all(
            "XPS Shipment Parcel",
            filters={"parent": shipment.name},
            fields=[
                "weight",
                "length",
                "width",
                "height",
                "insurance_amount",
                "declared_value"
            ]
        ):
            # Convert insurance_amount 0.00 to None
            insurance_amount = parcel.insurance_amount
            if insurance_amount in (0, 0.0, "0.00", None):
                insurance_amount = None

            # Convert declared_value 0.00 to None
            declared_value = parcel.declared_value
            if declared_value in (0, 0.0, "0.00", None):
                declared_value = None

            packages.append({
                "weight": parcel.weight,
                "length": parcel.length,
                "width": parcel.width,
                "height": parcel.height,
                "insuranceAmount": insurance_amount,
                "declaredValue": declared_value
            })

        order = {
            "orderId": shipment.name,
            "orderName": shipment.name,
            "orderDate": utc_timestamp,
            "shippingService": shipment.shipping_service or None,
            "shipperReference": delivery_notes[0].delivery_note if delivery_notes else None,
            "sender": {
                "name": pickup_address.address_title if pickup_address else "",
                "company": shipment.custom_attention,
                "address1": pickup_address.address_line1 if pickup_address else "",
                "address2": pickup_address.address_line2 if pickup_address else "",
                "city": pickup_address.city if pickup_address else "",
                "state": pickup_address.state if pickup_address else "",
                "country": pickup_country_code.upper() if pickup_address else "",
                "zip": pickup_address.pincode if pickup_address else "",
                "phone": pickup_address.phone if pickup_address else "",
                "email": pickup_address.email if pickup_address else ""
            },
            "receiver": {
                "name": delivery_address.address_title if delivery_address else "",
                "company": shipment.custom_attention,
                "address1": delivery_address.address_line1 if delivery_address else "",
                "address2": delivery_address.address_line2 if delivery_address else "",
                "city": delivery_address.city if delivery_address else "",
                "state": delivery_address.state if delivery_address else "",
                "country": delivery_country_code.upper() if delivery_address else "",
                "zip": delivery_address.pincode if delivery_address else "",
                "phone": delivery_address.phone if delivery_address else "",
                "email": delivery_address.email if delivery_address else ""
            },  
            "packages": packages if packages else []    
        }
        
        orders.append(order)
        
    data = {"orders": orders}

    # Return raw JSON directly
    return Response(
        json.dumps(data, ensure_ascii=False, indent=None),  
        mimetype='application/json'
    )
    
 

##################################################################################################
@frappe.whitelist(allow_guest=True,methods=["POST"])
def update_order():
    # --------------------------------------------------
    # 1️⃣ Security checks
    # --------------------------------------------------
    enabled = frappe.db.get_single_value("XPS Settings", "enable_webhook")
    if not enabled:
        frappe.throw(_("XPS Shipper WEBHOOK is not enabled."), frappe.PermissionError)

    received_secret = frappe.request.headers.get("x-rsis-key")
    expected_secret = frappe.db.get_single_value("XPS Settings", "webhook_secret_key")

    if not expected_secret or received_secret != expected_secret:
        frappe.throw(_("Invalid webhook secret"), frappe.AuthenticationError)

    # --------------------------------------------------
    # 2️⃣ Read payload (FORM-ENCODED)
    # --------------------------------------------------
    payload = frappe.form_dict.copy()

    shipment_name = payload.get("orderId")
    if not shipment_name:
        frappe.throw(_("orderId (XPS Shipment ID) is required"))

    # --------------------------------------------------
    # 3️⃣ Load XPS Shipment
    # --------------------------------------------------
    if not frappe.db.exists("XPS Shipment", shipment_name):
        frappe.throw(_("XPS Shipment {0} not found").format(shipment_name))

    shipment = frappe.get_doc("XPS Shipment", shipment_name)

    # --------------------------------------------------
    # 4️⃣ Update tracking numbers
    # --------------------------------------------------
    tracking_numbers = payload.get("trackingNumbers", "")
    if tracking_numbers:
        shipment.tracking_numbers = []

        for tn in tracking_numbers.split(","):
            shipment.append("tracking_numbers", {
                "tracking_number": tn.strip()
            })

    # --------------------------------------------------
    # 5️⃣ Save safely
    # --------------------------------------------------
    shipment.flags.ignore_permissions = True
    shipment.save()

    frappe.db.commit()

    return {
        "status": "OK",
        "shipment": shipment.name
    }
##################################################################################################
@frappe.whitelist(allow_guest=True)
def get_order():
    # Check if WEBHOOK integration is enabled
    enabled = frappe.db.get_single_value("XPS Settings", "enable_webhook")
    if not enabled:
        frappe.throw("XPS Shipper WEBHOOK is not enabled.", exc=frappe.PermissionError)

    # Verify secret
    received_secret = frappe.request.headers.get("x-rsis-key")
    expected_secret = frappe.db.get_single_value("XPS Settings", "webhook_secret_key")
    if not expected_secret or received_secret != expected_secret:
        frappe.throw("Invalid webhook secret", exc=frappe.AuthenticationError) 

    payload = frappe.request.get_json()
    frappe.log_error(title="XPS Get Order Webhook", message=str(payload))  # Debug log

    data = {"status": "received"}
    # Return raw JSON directly
    return Response(
        json.dumps(data, ensure_ascii=False, indent=None),  
        mimetype='application/json'
    )
