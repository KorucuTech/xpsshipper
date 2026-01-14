# XPS Web Shipper web site : https://www.xpsshipper.com/
# XPS Web Shipper eCommerce REST API documentation : https://xpsshipper.com/restapi/docs/v1-ecommerce/
# XPS Web Shipper Core REST API documentation : https://xpsshipper.com/restapi/docs/v1/


ECOMMERCE_API_ENDPOINTS = {
    "list_services": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/services"},
    "quote": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/quote"},
    "list_integrated_quoting_options": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integratedQuotingOptions"},
    "put_order": {"method": "PUT", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integrations/{integration_id}/orders/{order_id}"},
    "delete_order": {"method": "DELETE", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integrations/{integration_id}/orders/{order_id}"},
    "retrieve_shipment": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}"},
    "retrieve_shipping_label": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}/label/{label_format}"},
    "retrieve_shipments": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments?{parameters}"},
    "search_shipments": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/searchShipments"},
    "list_order_tags": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/list-tags"},
    "assign_tags_to_order": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integrations/{integration_id}/orders/{order_id}/assign-tags"},
    "unassign_tags_from_order": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integrations/{integration_id}/orders/{order_id}/unassign-tags"}
}

CORE_API_ENDPOINTS = {
    "create_customer": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers"},
    "connect_customer": {"method": "POST", "url": "{api_base_url}/restapi/v1/connect-customer"},
    "list_services": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/services"},
    "quote": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/quote"},
    "book_shipment": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments"},
    "retrieve_shipping_label": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}/label"},
    "retrieve_commercial_invoice": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}/commercialInvoice"},
    "retrieve_shipment": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}"},
    "retrieve_shipments": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments?{parameters}"},
    "search_shipments": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/searchShipments"},
    "void_shipment": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}"},
    "schedule_pickup": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/pickups"},
    "cancel_pickup": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/pickups/{pickup_id}"},
    "update_payment_method": {"method": "POST", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/paymentMethod"},
    "list_integrated_quoting_options": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/integratedQuotingOptions"},
    "list_provider_accounts": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/provider-accounts"},
    "put_provider_account": {"method": "PUT", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/provider-accounts/{provider_account_id}"},
    "delete_provider_account": {"method": "DELETE", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/provider-accounts/{provider_account_id}"},
    "search_sales_reps": {"method": "GET", "url": "{api_base_url}/restapi/v1/users/searchSalesReps?keyword={keyword}"},
    "track_shipment": {"method": "GET", "url": "{api_base_url}/restapi/v1/customers/{customer_id}/shipments/{book_id}/tracking-information"},
}

def build_endpoint(endpoints: dict, name: str, **kwargs) -> dict:

    if name not in endpoints:
        raise ValueError(f"Unknown endpoint: {name}")

    endpoint = endpoints[name]

    try:
        url = endpoint["url"].format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing URL parameter: {e}")

    return {
        "method": endpoint["method"],
        "url": url
    }

