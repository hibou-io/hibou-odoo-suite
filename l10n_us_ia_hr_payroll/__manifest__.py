{
    'name': 'USA - Iowa - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA - Iowa Payroll Rules.
==================================

* Contribution register and partner for Iowa Workforce Development (IWD) -  Unemployment
* Contribution register and partner for Iowa Department of Revenue (IDOR) - Income Tax Withholding
* Contract level Iowa Exemptions
* Company level Iowa Unemployment Rate
* Salary Structure for Iowa
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
