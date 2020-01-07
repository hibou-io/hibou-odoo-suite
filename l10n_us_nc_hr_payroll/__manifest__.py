{
    'name': 'USA - North Carolina - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA::North Carolina Payroll Rules.
==================================

* Contribution register and partner for North Carolina Department of Taxaction - Unemployment
* Contribution register and partner for North Carolina Department of Taxaction -  Income Tax Withholding
* Contract level North Carolina Exemptions
* Company level North Carolina Unemployment Rate
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
    'installable': False
}
