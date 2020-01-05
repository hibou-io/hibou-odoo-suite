# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'United States of America - Payroll with Accounting',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.2019.0.0',
    'category': 'Human Resources',
    'depends': [
        'l10n_us_hr_payroll',
        'hr_payroll_account',
        'l10n_generic_coa',
    ],
    'description': """
Accounting Data for USA Payroll Rules.
======================================
    """,
    'auto_install': True,
    'data': [
        'data/l10n_us_hr_payroll_account_data.xml',
    ],
    'demo': [
        'data/l10n_us_hr_payroll_account_demo.xml',
    ],
    'post_init_hook': '_post_install_hook_configure_journals',
    'license': 'OPL-1',
}
