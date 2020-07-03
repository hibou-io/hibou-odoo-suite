# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'RMA - Product Cores',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'license': 'OPL-1',
    'category': 'Tools',
    'summary': 'RMA Product Cores',
    'description': """
RMA Product Cores - Return core products from customers.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'product_cores',
        'rma_sale',
    ],
    'data': [
        'views/portal_templates.xml',
        'views/rma_views.xml',
        'wizard/rma_lines_views.xml',
    ],
    'demo': [
        'data/rma_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
