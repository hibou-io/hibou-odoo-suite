# © 2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Hibou RMAs',
    'version': '12.0.1.0.0',
    'category': 'Warehouse',
    'author': "Hibou Corp.",
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'depends': [
        'stock',
        'delivery',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'security/rma_security.xml',
        'views/rma_views.xml',
        'views/stock_picking_views.xml',
        'wizard/rma_lines_views.xml',
    ],
    'demo': [
        'data/rma_demo.xml',
    ],
    'installable': True,
    'application': True,
 }
