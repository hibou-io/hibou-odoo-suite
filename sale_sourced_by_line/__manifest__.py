{
    'name': 'Sale Sourced by Line',
    'summary': 'Multiple warehouse source locations for Sale order',
    'version': '13.0.1.0.0',
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
warehouse instead of using the warehouse of the sale order. Additionally, 
adds the ability to set the planned date of the outgoing shipments on a 
per order or per order line basis.

This module was inspired by a module by the same name from the OCA for 9.0, 
however it does not necessarily work in the same ways or have the same features.

""",
    'depends': [
        'sale_stock',
    ],
    'demo': [],
    'data': [
        'views/sale_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
