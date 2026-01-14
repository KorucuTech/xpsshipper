frappe.ui.form.on("Delivery Note", {
    refresh: function(frm) {
        // Only for submitted DNs
        if(frm.doc.docstatus === 1) {
            // Add to primary "Create" button group
            frm.add_custom_button(__('XPS Shipment'), function() {
                frappe.call({
                    method: "xpsshipper.api.check_xps_shipment_before_create",
                    args: { delivery_note: frm.doc.name },
                    callback: function(r) {
                        if(r.message.warning) {
                            frappe.confirm(
                                r.message.message + "\n\nDo you want to continue?",
                                function() {
                                    frappe.call({
                                        method: "xpsshipper.api.create_xps_shipment_from_dn",
                                        args: { delivery_note: frm.doc.name },
                                        callback: function(res) {
                                            frappe.set_route("Form", "XPS Shipment", res.message);
                                        }
                                    });
                                },
                                function() {
                                    frappe.msgprint("XPS Shipment creation cancelled.");
                                }
                            );
                        } else {
                            frappe.call({
                                method: "xpsshipper.api.create_xps_shipment_from_dn",
                                args: { delivery_note: frm.doc.name },
                                callback: function(res) {
                                    frappe.set_route("Form", "XPS Shipment", res.message);
                                }
                            });
                        }
                    }
                });
            }, __("Create"), true); // <--- 'true' adds it to the primary button group
        }
    }
});
