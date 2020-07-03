# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou RMAs for Sale Orders',
    'version': '13.0.1.1.0',
    'category': 'Sale',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        'rma',
        'sale',
        'sales_team',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_templates.xml',
        'views/product_views.xml',
        'views/rma_views.xml',
        'views/sale_views.xml',
        'wizard/rma_lines_views.xml',
    ],
    'demo': [
        'data/rma_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
 }
