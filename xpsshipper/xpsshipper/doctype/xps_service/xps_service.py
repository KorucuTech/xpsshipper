# Copyright (c) 2026, Kemal Korucu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from xpsshipper.api import call_xps_api


class XPSService(Document):
    pass


@frappe.whitelist()
def sync_xps_services():
    """
    Sync XPS services into local DocType (upsert)
    Preserves 'enabled' state for existing services
    Syncs child tables:
      - XPS Signature Option
      - XPS Package Type
    """

    response = call_xps_api("list_services")
    services = response.get("services", [])

    existing = {
        d.service_code: {
            "name": d.name,
            "enabled": d.enabled
        }
        for d in frappe.get_all(
            "XPS Service",
            fields=["name", "service_code", "enabled"]
        )
    }

    for svc in services:
        service_code = svc.get("serviceCode")
        enabled = existing.get(service_code, {}).get("enabled", 1)

        values = {
            "service_code": service_code,
            "service_label": svc.get("serviceLabel"),
            "carrier_code": svc.get("carrierCode"),
            "carrier_label": svc.get("carrierLabel"),
            "inbound": svc.get("inbound", 0),
            "supported_countries": ", ".join(svc.get("supportedCountries") or []),
            "unsupported_countries": ", ".join(svc.get("unsupportedCountries") or []),
            "enabled": enabled
        }

        # Fetch or create parent doc
        if service_code in existing:
            doc = frappe.get_doc("XPS Service", existing[service_code]["name"])
            doc.update(values)
        else:
            doc = frappe.get_doc({
                "doctype": "XPS Service",
                **values
            })

        # -----------------------------
        # Sync Signature Options
        # -----------------------------
        doc.signature_options = []

        for opt in svc.get("signatureOptions") or []:
            doc.append("signature_options", {
                "signature_option_code": opt.get("signatureOptionCode"),
                "signature_option_label": opt.get("signatureOptionLabel"),
            })

        # -----------------------------
        # Sync Package Types
        # -----------------------------
        doc.package_types = []

        for pkg in svc.get("packageTypes") or []:
            doc.append("package_types", {
                "package_type_code": pkg.get("packageTypeCode"),
                "package_type_label": pkg.get("packageTypeLabel"),
                "multipiece_supported": pkg.get("multipieceSupported"),
                "weight_unit": pkg.get("weightUnit"),
                "max_weight_per_piece": pkg.get("maxWeightPerPiece"),
                "dim_type": pkg.get("dimType"),
                "dim_unit": pkg.get("dimUnit"),
                "preset_length": pkg.get("presetLength"),
                "preset_width": pkg.get("presetWidth"),
                "preset_height": pkg.get("presetHeight"),
            })

        doc.save(ignore_permissions=True)

    frappe.db.commit()

