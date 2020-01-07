{
    'name': 'USA - Missouri - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
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
        'views/hr_payroll_views.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': False
}
