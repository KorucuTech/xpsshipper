frappe.listview_settings['XPS Service'] = {
    onload: function(listview) {
        // Make sure the page is fully initialized
        listview.page.set_primary_action(__('Sync from XPS'), () => {
            frappe.confirm(
                __('Fetch and update services from XPS?'),
                () => {
                    frappe.call({
                        method: 'xpsshipper.xpsshipper.doctype.xps_service.xps_service.sync_xps_services',
                        freeze: true,
                        freeze_message: __('Syncing XPS services...'),
                        callback: function(r) {
                            frappe.show_alert({
                                message: __('{0} services synced', [r.message || 0]),
                                indicator: 'green'
                            });
                            listview.refresh();
                        }
                    });
                }
            );
        });
    }
};
