{
    'name': 'Project Stages',
    'version': '13.0.1.0.1',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Adds stages to Projects themselves.
    """,
    'depends': [
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
