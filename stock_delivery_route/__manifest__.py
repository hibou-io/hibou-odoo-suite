{
    'name': 'Warehouse Delivery Routes',
    'summary': 'Assign a delivery route to a sale order or picking.',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp. <hello@hibou.io>",
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'complexity': 'expert',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Warehouse Delivery Routes
=========================

Assign a delivery route at the time of sale order.
Additionally, set a default route on the customer level.

""",
    'depends': [
        'sale_stock',
        'stock_picking_batch',
    ],
    'demo': [],
    'data': [
        'views/partner_views.xml',
        'views/sale_views.xml',
        'views/stock_views.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'installable': True,
}
