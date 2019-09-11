{
    'name': 'HR Expense Lead',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Assign Opportunity/Lead to expenses for reporting.',
    'description': """
Assign Opportunity/Lead to expenses for reporting.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'hr_expense',
        'crm',
    ],
    'data': [
        'views/hr_expense_views.xml',
        'views/crm_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
