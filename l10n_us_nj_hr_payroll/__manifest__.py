{
    'name': 'USA - New Jersey - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '11.0.2018.0.0',
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
        'us_nj_hr_payroll_view.xml',
        'data/base.xml',
        'data/rules_2018.xml',
        'data/final.xml',
    ],
    'installable': True
}
