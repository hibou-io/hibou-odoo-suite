{
    'name': 'Maintenance Notebook',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Record time on maintenance requests.',
    'description': """
Maintenance Notebook
====================

Adds a 'notebook' XML element to the Maintenance form to add pages in other modules.
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
