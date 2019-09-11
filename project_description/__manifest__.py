{
    'name': 'Project Description',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Adds description onto Projects that will be displayed on tasks.  
Useful for keeping project specific notes that are needed whenever 
you're working on a task in that project.
    """,
    'depends': [
        'project',
    ],
    'data': [
        'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
