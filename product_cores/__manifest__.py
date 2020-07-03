# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Product Cores',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'license': 'OPL-1',
    'summary': 'Charge customers core deposits.',
    'description': """
Charge customers core deposits.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'sale_stock',
        'purchase',
    ],
    'data': [
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
    ],
    'installable': True,
    'application': False,
}
