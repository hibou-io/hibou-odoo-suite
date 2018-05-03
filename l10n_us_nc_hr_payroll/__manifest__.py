{
    'name': 'USA - North Carolina - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
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
        'hr_payroll_view.xml',
        'data/base.xml',
        'data/rules_2018.xml',
        'data/final.xml',
    ],
    'installable': True
}
