{
    'name': 'HR Holidays Partial',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '11.0.0.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Partial day leave requests displau hours',
    'description': """
Create and display leave requests in hours for partial days.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_holidays_views.xml',
        ],
    'installable': True,
    'application': False,
}
