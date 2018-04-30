# -*- encoding: utf-8 -*-
{
    'name': 'USA - Virginia - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '10.0.2018.0.0',
    'description': """
USA::Virginia Payroll Rules.
============================

* Contribution register and partner for Virginia Department of Taxaction - Unemployment
* Contribution register and partner for Virginia Department of Taxaction -  Income Tax Withholding
* Contract level Virginia Exemptions
* Company level Virginia Unemployment Rate
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
