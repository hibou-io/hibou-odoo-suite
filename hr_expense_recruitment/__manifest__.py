{
    'name': 'HR Expense Recruitment',
    'version': '11.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Assign Recruitment to expenses for reporting.',
    'description': """
Assign Recruitment to expenses for reporting.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'hr_expense',
        'hr_recruitment',
    ],
    'data': [
        'views/hr_expense_views.xml',
        'views/hr_job_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
