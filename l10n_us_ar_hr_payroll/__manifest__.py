{
    'name': 'USA - Arkansas - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2019.0.0',
    'description': """
USA::Arkansas Payroll Rules.
==================================

* Contribution register and partner for Arkansas Department of Financial Administration - Income Tax Withholding
* Contribution register and partner for Arkansas Department of Workforce Solutions -  Unemployment
* Contract level Arkansas Exemptions
* Company level Arkansas Unemployment Rate
* Salary Structure for Arkansas
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
