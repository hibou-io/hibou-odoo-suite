{
    'name': 'Date on Payslip Lines',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr_payroll_account'],
    'version': '13.0.1.0.0',
    'description': """
Date on Payslip Lines
=====================

* Adds "Date Account" (date) field to payslip line from payslip
* Adds group by date to Payslip Line search view
* Allows filtering by "Date Account" for easy period reporting
    """,

    'auto_install': True,
    'website': 'https://hibou.io/',
    'data': [
        'payslip_view.xml',
    ],
    'installable': True
}
