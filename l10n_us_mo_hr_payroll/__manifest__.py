# -*- encoding: utf-8 -*-
{
    'name': 'USA - Missouri - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
    'description': """
USA::Missouri Payroll Rules.
============================

* Contribution register and partner for Missouri Department of Revenue - Unemployment
* Contribution register and partner for Missouri Department of Revenue -  Income Tax Withholding
* Contract level Missouri Exemptions and MO W-4 fields
* Company level Missouri Unemployment Rate
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
