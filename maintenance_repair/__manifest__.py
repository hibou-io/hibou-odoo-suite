{
    'name': 'Equipment Repair',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Consume products on Maintenance Requests',
    'description': """
Equipment Repair
================

Keep track of parts required to repair equipment.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'stock',
        'maintenance_notebook',
        'hr_department_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
