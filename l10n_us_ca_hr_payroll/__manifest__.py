{
    'name': 'USA - California - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.1.0',
    'description': """
USA::California Payroll Rules.
==============================

* Contribution register and partner for California Department of Taxation - Unemployment Insurance Tax
* Contribution register and partner for California Department of Taxation -  Income Tax Withholding
* Contribution register and partner for Califronia Department of Taxation - Employee Training Tax
* Contribution register and partner for Califronia Department of Taxation - State Disability Insurance
* Contract level California Exemptions
* Contract level California State Disability Insurance
* Company level California Unemployment Insurance Tax
* Company level California Employee Training Tax
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
