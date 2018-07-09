{
    'name': 'USA - Pennsylvania - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
    'description': """
USA::Pennsylvania Payroll Rules.
================================

* Partner for Pennsylvania Department of Revenue
* Contribution register for Pennsylvania Department of Revenue - Unemployment Insurance
* Contribution register Pennsylvania Department of Revenue - State Income Tax
* Contract level Pennsylvania Unemployment Rate
* Company level Pennsylvania Unemployement Rate
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
