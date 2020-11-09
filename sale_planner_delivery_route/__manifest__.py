{
    'name': 'Sale Order Planner - Delivery Route',
    'summary': 'Plans to the closest delivery route.',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Sale',
    'license': 'AGPL-3',
    'complexity': 'expert',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Sale Order Planner - Delivery Route
===================================

Plans to the closest delivery route.

""",
    'depends': [
        'stock_delivery_route',
        'sale_planner',
    ],
    'demo': [],
    'data': [
        'wizard/order_planner_views.xml',
        'views/stock_views.xml',
    ],
    'auto_install': True,
    'installable': True,
}
