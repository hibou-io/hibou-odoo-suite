# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'USA - 401K Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '15.0.1.0.0',
    'category': 'Payroll',
    'depends': [
        'l10n_us_hr_payroll',
    ],
    'description': """
* Adds fields to HR Contract for amount or percentage to withhold for retirement savings.
* Adds rules to withhold and have a company match.
    """,

    'data': [
        'data/payroll.xml',
        'views/contract_views.xml',
        'views/payroll_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'license': 'OPL-1',
}
