{
    'name': 'Stock Delivery Planner',
    'summary': 'Get rates and choose carrier for delivery.',
    'version': '12.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'website': "https://hibou.io",
    'description': """
Stock Delivery Planner
======================

Re-rate deliveries at packing time to find lowest-priced delivery method that still meets the expected delivery date.

""",
    'depends': [
        # 'sale_sourced_by_line',
        # 'base_geolocalize',
        # 'delivery',
        # 'resource',
        'delivery_hibou',
        'sale_planner',
        'stock',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/order_planner_views.xml',
        # 'views/sale.xml',
        'views/stock_views.xml',
        'wizard/stock_delivery_planner_views.xml',
        # 'views/delivery.xml',
        # 'views/product.xml',
    ],
    'auto_install': False,
    'installable': True,
}
