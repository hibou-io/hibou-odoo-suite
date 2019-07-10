{
    'name': 'USA - South Carolina - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2019.0.0',
    'description': """
USA::South Carolina Payroll Rules.
==================================
* Added Tax Rules, Salary Structure, and other tax related changes for South Carolina
* Contribution register and partner for South Carolina Department of Revenue
* Contribution register and partner for South Carolina Department of Employment and Workforce
* Rate for Unemployment with wage cap
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data': [
        'views/hr_payroll_views.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': True
}
