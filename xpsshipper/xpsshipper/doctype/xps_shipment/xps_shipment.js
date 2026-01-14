frappe.ui.form.on("XPS Shipment", {
    setup(frm) {
        set_dn_query(frm);
    },

    refresh(frm) {
        set_dn_query(frm);

        // Render addresses on load/refresh
        update_address_html(frm, "sender_address_name", "sender_address");
        update_address_html(frm, "receiver_address_name", "receiver_address");
    },

    customer(frm) {
        if (frm.doc.delivery_notes && frm.doc.delivery_notes.length) {
            frm.clear_table("delivery_notes");
            frm.refresh_field("delivery_notes");
            frappe.msgprint(__('Delivery Notes cleared because Customer changed.'));
        }
        set_dn_query(frm);
    },

    // NEW: sender address
    sender_address_name(frm) {
        update_address_html(frm, "sender_address_name", "sender_address");
    },

    // NEW: receiver address
    receiver_address_name(frm) {
        update_address_html(frm, "receiver_address_name", "receiver_address");
    }
});

/* --------------------------------------------------
 * Delivery Note + Service filtering (existing logic)
 * -------------------------------------------------- */
function set_dn_query(frm) {
    frm.fields_dict["delivery_notes"].grid
        .get_field("delivery_note").get_query = function (doc) {

            if (!doc.customer) {
                frappe.msgprint(__('Please select a Customer first.'));
                return { filters: { name: "" } };
            }

            const existing_dns = (doc.delivery_notes || [])
                .map(row => row.delivery_note)
                .filter(Boolean);

            return {
                filters: [
                    ["Delivery Note", "customer", "=", doc.customer],
                    ["Delivery Note", "docstatus", "=", 1],
                    ["Delivery Note", "name", "not in", existing_dns]
                ]
            };
        };

    frm.set_query("xps_service", () => {
        return {
            filters: {
                enabled: 1
            }
        };
    });
}

/* --------------------------------------------------
 * NEW: Shared Address Renderer (DRY)
 * -------------------------------------------------- */
function update_address_html(frm, link_field, html_field) {
    const address_name = frm.doc[link_field];

    if (!address_name) {
        frm.set_df_property(html_field, "options", "");
        return;
    }

    frappe.db.get_doc("Address", address_name)
        .then(address => {
            frm.set_df_property(html_field, "options", format_address(address));
        });
}

function format_address(address) {
    return `
        <div class="address-box">
            <strong>${address.address_title || ""}</strong><br>
            ${address.address_line1 || ""}<br>
            ${address.address_line2 ? address.address_line2 + "<br>" : ""}
            ${address.city || ""}${address.city && address.state ? ", " : ""}${address.state || ""}<br>
            ${address.pincode || ""}<br>
            ${address.country || ""}<br>
            ${address.phone ? "<strong>Phone:</strong> " + address.phone + "<br>" : ""}
            ${address.email_id ? "<strong>Email:</strong> " + address.email_id + "<br>" : ""}
        </div>
    `;
}
