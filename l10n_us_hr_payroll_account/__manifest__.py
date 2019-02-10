{
    'name': 'USA - Payroll with Accounting',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['l10n_us_hr_payroll', 'hr_payroll_account'],
    'version': '12.0.2019.0.0',
    'description': """
USA Payroll Accounting hooks.
=============================

    * Links Rules to Accounts based on US Accounting Localization
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data':[
        'l10n_us_hr_payroll_account_data.xml',
    ],
    'installable': True
}
