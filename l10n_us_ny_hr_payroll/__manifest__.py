{
    'name': 'USA - New York - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
    'description': """
USA::New York Payroll Rules.
==============================

* New Jersey Department of Taxation and Finance partner
* Contribution register and partner for New York State Department of Taxation and Finance
* Company level New York Unemployment Rate
* Company Level New York Re-employment Service Fund
* Company level New York Metropolitan Commuter Transportation Mobility Tax
* Contract level New York Income Tax
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data': [
        'hr_payroll_view.xml',
        'data/base.xml',
        'data/rules_2018.xml',
        'data/final.xml',
    ],
    'installable': False
}
