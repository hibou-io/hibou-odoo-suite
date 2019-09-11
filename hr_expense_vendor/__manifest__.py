{
    'name': 'HR Expense Vendor',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Record the vendor paid on expenses.',
    'description': """
Record the vendor paid on expenses.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'hr_expense',
    ],
    'data': [
        'views/hr_expense_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
