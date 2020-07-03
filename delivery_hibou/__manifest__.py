{
    'name': 'Delivery Hibou',
    'summary': 'Adds underlying pinnings for things like "RMA Return Labels"',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Stock',
    'license': 'AGPL-3',
    'images': [],
    'website': "https://hibou.io",
    'description': """
This is a collection of "typical" carrier needs, and a bridge into Hibou modules like `delivery_partner` and `sale_planner`.
""",
    'depends': [
        'delivery',
        'delivery_partner',
    ],
    'demo': [],
    'data': [
        'views/delivery_views.xml',
        'views/stock_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
