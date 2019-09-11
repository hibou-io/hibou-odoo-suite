{
    'name': 'Project Task Lines',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Adds "todo" lines onto Project Tasks, and improves sub-tasks.
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
