# -*- encoding: utf-8 -*-
{
    'name': 'USA - Texas - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
    'description': """
USA::Texas Payroll Rules.
=========================

    * Texas Workforce Commission partner
    * Contribution register for Texas Workforce Commission
    * Company level Texas Umemployment Rate
    * Company level Texas Obligation Assessment Rate
    * Company level Texas Employment & Training Investment Assessment
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data':[
        'us_tx_hr_payroll_view.xml',
        'data/base.xml',
        'data/rules_2018.xml',
        'data/final.xml',
    ],
    'installable': True
}
