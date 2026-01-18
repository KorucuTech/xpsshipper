frappe.ui.form.on("XPS Shipment", {
    // Triggered whenever the form is loaded or refreshed
    onload: function(frm) {
        frm._package_type_cache = {}; // Client-side cache for options
        populate_package_type(frm);
    },

    // Triggered whenever the shipping_service field is changed
    shipping_service: function(frm) {
        populate_package_type(frm);
    }
});

/**
 * Populate package_type options based on the shipping_service
 * - Uses client-side caching to avoid repeated server calls
 * - Clears package_type if current value is invalid
 * - Disables field while loading options
 */
function populate_package_type(frm) {
    const service = frm.doc.shipping_service;

    // Reset package_type first
    frm.set_value("package_type", "");
    frm.set_df_property("package_type", "options", []);
    frm.refresh_field("package_type");

    if (!service) {
        return;
    }

    // Check cache first
    if (frm._package_type_cache[service]) {
        set_package_type_options(frm, frm._package_type_cache[service]);
        return;
    }

    // Disable field while fetching
    frm.set_df_property("package_type", "read_only", 1);

    frappe.call({
        method: "xpsshipper.xpsshipper.doctype.xps_shipment.xps_shipment.get_package_type_options",
        args: { service: service },
        callback: function(r) {
            const options = r.message || [];

            // Cache options for this service
            frm._package_type_cache[service] = options;

            set_package_type_options(frm, options);
        },
        error: function() {
            frappe.msgprint(__("Failed to fetch package type options"));
            frm.set_df_property("package_type", "read_only", 0);
        }
    });
}

/**
 * Helper function to update the package_type field
 */
function set_package_type_options(frm, options) {
    frm.set_df_property("package_type", "options", options.join("\n"));
    frm.set_df_property("package_type", "read_only", 0);
    frm.refresh_field("package_type");

    // Clear value if current package_type is no longer valid
    if (!options.includes(frm.doc.package_type)) {
        frm.set_value("package_type", "");
    }
}
