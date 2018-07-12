{
    'name': 'HR Holidays Accrual - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '11.0.0.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Grant leave allocations per payperiod',
    'description': """
Automates leave allocations.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr_holidays_accrual',
        'hr_payroll'
    ],
    'data': [
        'views/hr_holidays_views.xml',
        ],
    'installable': True,
    'application': False,
}
