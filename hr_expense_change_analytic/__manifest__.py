{
    'name': 'HR Expense Change - Analytic',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Employees',
    'sequence': 96,
    'summary': 'Change Analytic Account on Expense.',
    'description': """
Adds fields and functionality to change the analytic account on expense 
and subsequent documents.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr_expense_change',
        'analytic',
    ],
    'data': [
        'wizard/expense_change_views.xml',
    ],
    'installable': True,
    'application': False,
}
