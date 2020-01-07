{
    'name': 'USA - Minnesota - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll'],
    'version': '12.0.2019.0.0',
    'description': """
USA - Minnesota Payroll Rules
=============================

* Contribution register and partner for Minnesota Department of Revenue (MDOR) - Income Tax Withholding
* Contribution register and partner for Minnesota Unemployment Insurance (MUI) -  Unemployment Taxes
* Contract level Minnesota Allowances, Additional Withholding, Filing Status

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
