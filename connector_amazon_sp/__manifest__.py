{
    "name": "Amazon Selling Partner Connector",
    "version": "11.0.1.0.0",
    "depends": [
        "connector_ecommerce",
        "sale_order_dates",
        "sale_sourced_by_line",
        "delivery_hibou",
        "sale_planner",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/connector_amazon_sp_data.xml",
        "views/amazon_menus.xml",
        "views/amazon_backend_views.xml",
        "views/amazon_feed_views.xml",
        "views/amazon_product_views.xml",
        "views/amazon_sale_views.xml",
        "views/delivery_carrier_views.xml",
        "views/stock_views.xml",
    ],
    "author": "Hibou Corp.",
    "license": "LGPL-3",
    "description": """
Amazon Selling Partner Connector
================================

* Import Orders from your Amazon Marketplaces.
* Deliver Amazon orders by purchasing shipping via the MerchantFulfillment API.
* Manage Listing SKUs and inventory. (Supports multiple warehouses via SKU+WH_Code)
* Manage Listing Pricing including using Price Lists

    """,
    "summary": "",
    "website": "https://hibou.io/",
    "category": "Tools",
    "auto_install": False,
    "installable": True,
    "application": True,
    "external_dependencies": {
        "python": [
            "sp_api",
        ],
    },
}
