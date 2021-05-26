# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Canada - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '14.0.2021.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll_hibou',
    ],
    'description': """
Canada - Payroll Rules.
=======================

    """,

    'data': [
        'security/ir.model.access.csv',
        'data/base.xml',
        'data/federal.xml',
        'data/ca_cpp.xml',
        # 'views/hr_contract_views.xml',
        # 'views/ca_payroll_config_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'post_init_hook': '_post_install_hook',
    'license': 'OPL-1',
}
