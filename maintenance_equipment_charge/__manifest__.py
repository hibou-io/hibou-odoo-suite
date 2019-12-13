{
    'name': 'Equipment Charges',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Record related equipment charges.',
    'description': """
Equipment Charges
=================

Record related equipment charges, for example fuel charges.
""",
    'website': 'https://www.odoo.com/page/manufacturing',
    'depends': [
        'hr_maintenance',
        'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
