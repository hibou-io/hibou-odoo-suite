# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Stock Exception Rule',
    'version': '16.0.1.0.0',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': 'Custom exceptions on delivery orders',
    'description': """
Custom exceptions on delivery orders
""",
    'website': 'https://hibou.io/',
    'depends': [
        'base_exception_user',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_views.xml',
        'wizard/stock_exception_confirm_views.xml',
    ],
    'demo': [
        'demo/stock_exception_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
