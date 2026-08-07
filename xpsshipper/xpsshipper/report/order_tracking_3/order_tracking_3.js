frappe.query_reports["Order Tracking 3"] = {
    onload: function(report) {
        let today = frappe.datetime.get_today();
        let ninety_days_ago = frappe.datetime.add_days(today, -90);

        report.set_filter_value("so_date_from", ninety_days_ago);
        report.set_filter_value("so_date_thru", today);
        report.set_filter_value("include_submitted", 1);
        report.set_filter_value("include_draft", 0);
        report.set_filter_value("include_canceled", 0);
    }
};