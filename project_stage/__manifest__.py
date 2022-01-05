{
    'name': 'Project Stages (deprecated)',
    'version': '15.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Adds stages to Projects themselves. (deprecated)
After upgrade you can uninstall.
    """,
    'depends': [
        'project',
    ],
    'data': [
        # Deprecated in 15.0, 
        # this will uninstall the views/security rules for a model that will not exist after upgrade.
        'security/ir.model.access.csv',
        # 'views/project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
