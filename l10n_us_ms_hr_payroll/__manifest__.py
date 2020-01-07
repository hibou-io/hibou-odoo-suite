{
    'name': 'USA - Mississippi - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA::Mississippi Payroll Rules.
===============================

* New Partners and Contribution Registers for:
     * Mississippi Department of Revenue
     * Mississippi Department of Employment Security
* Contract level Mississippi Exemptions and 89-350 fields
* Payroll Rate for Mississippi Unemployment Rate
    """,
    'auto_install': False,
    'website': 'https://hibou.io/',
    'data': [
        'views/hr_payroll_views.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': False
}
