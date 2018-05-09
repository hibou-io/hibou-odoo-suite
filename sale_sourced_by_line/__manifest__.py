{
    'name': 'Sale Sourced by Line',
    'summary': 'Multiple warehouse source locations for Sale order',
    'version': '11.0.1.0.0',
    'author': "Hibou Corp.,Odoo Community Association (OCA)",
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'complexity': 'expert',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Sale Sourced by Line
====================

Adds the possibility to source a line of sale order from a specific
warehouse instead of using the warehouse of the sale order.

""",
    'depends': [
        'sale_stock',
        'sale_order_dates',
    ],
    'demo': [],
    'data': [
        'views/sale_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
