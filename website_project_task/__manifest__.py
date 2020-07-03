{
    'name': 'Website Project Tasks',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
This module adds options to Website Project:
============================================

* Tags on Tasks
* Classes on Stages and Tags for CSS hooks.
    """,
    'depends': [
        'project',
    ],
    'data': [
        'views/project_task_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'category': 'Hidden',
}
