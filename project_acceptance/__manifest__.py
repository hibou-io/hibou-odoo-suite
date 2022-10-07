{
    'name': 'Project Acceptance',
    'version': '15.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """    """,
    'depends': [
        # 'project',
        'project_exception',
    ],
    'data': [
        'data/mail_template_data.xml',
        'data/project_exception_data.xml',
        # 'report/project_report.xml',
        # 'report/project_report_template.xml',        
        'views/project_portal_templates.xml',
        'views/project_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}