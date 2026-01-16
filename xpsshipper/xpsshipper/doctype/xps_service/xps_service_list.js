frappe.listview_settings['XPS Service'] = {
    onload(listview) {
        listview.page.add_inner_button(__('Sync from XPS'), () => {
            frappe.confirm(
                __('Fetch and update services from XPS?'),
                () => {
                    frappe.call({
                        method: 'xpsshipper.xpsshipper.doctype.xps_service.xps_service.sync_xps_services',
                        freeze: true,
                        freeze_message: __('Syncing XPS services...'),
                        callback(r) {
                            frappe.show_alert({
                                message: __('XPS services synced successfully'),
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
