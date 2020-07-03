# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Website Product Cores',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'category': 'Website',
    'description': """
Removes Trash icon from Core Product
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'product_cores',
        'website_sale',
    ],
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
