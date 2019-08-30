{
    'name': 'HR Department Project',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Provide default project per Department',
    'description': """
HR Department Project
=====================

Define a 'default project' for every department.  This is a bridge module to allow other modules to use this behavior.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'project',
        'hr',
    ],
    'data': [
        'views/hr_views.xml',
        'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
