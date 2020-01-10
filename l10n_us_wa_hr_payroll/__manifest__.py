{
    'name': 'USA - Washington - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
    'description': """
USA::Washington Payroll Rules.
==============================

* Contribution register and partner for Washington Employment Security Department - Unemployment
* Contribution register and partner for Washington Labor & Industries -  (LNI)
* Contract level LNI
* Company level Washington Unemployment Rate
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data': [
        'security/ir.model.access.csv',
        'hr_payroll_view.xml',
        'data/base.xml',
        'data/rules_2018.xml',
        'data/final.xml',
    ],
    'installable': False
}
