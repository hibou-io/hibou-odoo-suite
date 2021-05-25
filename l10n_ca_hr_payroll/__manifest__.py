# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Canada - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '14.0.2020.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll_hibou',
    ],
    'description': """
Canada - Payroll Rules.
=========================================

    """,

    'data': [
        'data/base.xml',
        'data/federal.xml',
        'security/ir.model.access.csv',
        # 'views/hr_contract_views.xml',
        # 'views/us_payroll_config_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'post_init_hook': '_post_install_hook',
    'license': 'OPL-1',
}
