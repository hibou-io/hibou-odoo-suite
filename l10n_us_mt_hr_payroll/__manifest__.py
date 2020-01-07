{
    'name': 'USA - Montana - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA::Montana Payroll Rules.
===========================

* New Partners and Contribution Registers for:
     * Montana Department of Revenue
     * Montana Department of Labor & Industry
* Contract level Montana Exemptions and MW-4 fields
* Payroll Rate for Montana L&I Unemployment Rate
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
