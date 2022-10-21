{
    'name': 'Payroll Report Year to Date',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Show YTD computations on Payslip Report',
    'description': """
Show Year to Date (YTD) computations on Payslip Report.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_payroll'],
    'data': [
        'views/payslip_views.xml',
    ],
    'installable': True,
    'application': False,
}
