{
    'name': 'USA - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['hr_payroll', 'hr_payroll_rate'],
    'version': '12.0.2019.1.0',
    'description': """
USA Payroll Rules.
==================

    * Contract W4 Filing Status & Allowances
    * FICA Social Security (with wages cap)
    * FICA Medicare
    * FICA Additioal Medicare Wages & Tax
    * FUTA Federal Unemployment (with wages cap)
    * Federal Income Tax Withholdings based on W4 values
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data': [
        'views/l10n_us_hr_payroll_view.xml',
        'data/base.xml',
        'data/rates.xml',
        'data/rules.xml',
        'data/final.xml',
    ],
    'installable': True
}
