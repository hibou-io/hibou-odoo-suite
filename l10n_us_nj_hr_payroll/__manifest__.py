{
    'name': 'USA - New Jersey - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA::New Jersey Payroll Rules.
==============================

    * New Jersey Division of Taxation partner
    * Contribution register for New Jersey DoT
    * Company level New Jersey Unemployment Rate
    * Company level New Jersey State Disability Insurance Rate
    * Contract level New Jersey Unemployment Rate
    * Contract level New Jersey State Disability Insurance Rate
    * Contract level New Jersey Family Leave Insurance Rate
    * Contract level New Jersey Workforce Development/Supplemental Workforce Funds
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data':[
        'views/us_nj_hr_payroll_views.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': False
}
