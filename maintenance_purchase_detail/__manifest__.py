{
    'name': 'Equipment Purchase Detail',
    'version': '20.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'summary': 'Record purchase date and details on Equipments.',
    'description': """
Equipment Purchase Detail
=========================

Adds fields for purchase date, and condition on the Equipment form.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'maintenance',
    ],
    'data': [
        'views/maintenance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
