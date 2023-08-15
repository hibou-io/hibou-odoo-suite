{
    'name': 'Website Project Tasks',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'version': '16.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'summary': 'Adds tags on tasks, classes on stages and tags for CSS hooks in Website Project.',
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
