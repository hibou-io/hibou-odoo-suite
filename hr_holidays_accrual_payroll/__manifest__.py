{
    'name': 'HR Holidays Accrual - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '12.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Grant leave allocations per payperiod',
    'description': """
Automates leave allocations.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr_holidays',
        'hr_payroll'
    ],
    'data': [
        'views/hr_holidays_views.xml',
        ],
    'installable': True,
    'application': False,
}
