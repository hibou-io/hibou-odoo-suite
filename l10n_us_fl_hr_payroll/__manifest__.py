{
    'name': 'USA - Florida - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA::Florida Payroll Rules.
===========================

    * Florida Department of Revenue partner
    * Contribution register for Florida DoR
    * Company level Florida Unemployment Rate
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data':[
        'views/us_fl_hr_payroll_views.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': False
}
