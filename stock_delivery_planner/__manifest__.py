{
    'name': 'Stock Delivery Planner',
    'summary': 'Get rates and choose carrier for delivery.',
    'version': '15.0.1.1.0',
    'author': "Hibou Corp.",
    'category': 'Warehouse',
    'license': 'OPL-1',
    'website': "https://hibou.io",
    'description': """
Stock Delivery Planner
======================

Re-rate deliveries at packing time to find lowest-priced delivery method that still meets the expected delivery date.

""",
    'depends': [
        'delivery_hibou',
        'sale_planner',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stock_views.xml',
        'wizard/stock_delivery_planner_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
