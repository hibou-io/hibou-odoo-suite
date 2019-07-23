{
    'name': 'HR Holidays Accrual',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '12.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Grant leave allocations with tags',
    'description': """
Create leave allocations by tag, then use tags to grant leaves to employees.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_holidays_views.xml',
        ],
    'installable': False,
    'application': False,
}
