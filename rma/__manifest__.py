# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou RMAs',
    'version': '13.0.1.2.0',
    'category': 'Warehouse',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        'stock',
        'delivery',
    ],
    'demo': [
        'demo/rma_demo.xml',
    ],
    'data': [
        'data/cron_data.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/rma_security.xml',
        'views/account_views.xml',
        'views/portal_templates.xml',
        'views/rma_views.xml',
        'views/stock_picking_views.xml',
        'wizard/rma_lines_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
 }
