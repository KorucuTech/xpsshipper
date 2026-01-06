// Copyright (c) 2026, Kemal Korucu and contributors
// For license information, please see license.txt

frappe.ui.form.on('XPS Settings', {
    refresh: function(frm) {
        // Target the button field
        const btn_field = frm.fields_dict.test_api_access;
        if (!btn_field) return;

        // Remove any old click handlers
        btn_field.$wrapper.find('.btn').off('click');

        // Add new click handler
        btn_field.$wrapper.find('.btn').on('click', function() {
            console.log("🚀 Test API Access button clicked!");

            // Basic client validation
            if (!frm.doc.api_key || !frm.doc.customer_id || !frm.doc.api_base_url) {
                frappe.msgprint("Please fill API Key, Customer ID, and API Base URL first.");
                return;
            }

            frappe.call({
                method: "xpsshipper.xpsshipper.doctype.xps_settings.xps_settings.test_api_access",
                // If your folder is apps/xpsshipper/doctype/... (no extra module), try:
                // method: "xpsshipper.doctype.xps_settings.xps_settings.test_api_access",
                args: { docname: frm.doc.name },
                freeze: true,
                freeze_message: __("Testing API connection... Please wait"),
                callback: function(r) {
                    console.log("✅ Server response:", r);
                    // msgprint already shows success/error
                    frm.refresh();
                },
                error: function(r) {
                    console.error("❌ Server error (likely wrong method path):", r);
                    frappe.msgprint({
                        title: __("Call Failed"),
                        message: __("Check browser console (F12) for details. Common fix: wrong method path in .js file."),
                        indicator: "red"
                    });
                }
            });
        });
    }
});