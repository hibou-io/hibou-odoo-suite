# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Peru - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '15.0.2022.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll_hibou',
        'hr_contract_reports',
        'hibou_professional',
    ],
    'description': """
Peru - Payroll Rules.
=====================

    """,

    'data': [
        'security/ir.model.access.csv',
        'data/base.xml',
        'data/integration_rules.xml',
        'data/afp_rules.xml',
        'data/onp_rules.xml',
        'data/ir_4ta_cat_rules.xml',
        'data/ir_5ta_cat_rules.xml',
        'data/er_rules.xml',
        'views/hr_contract_views.xml',
        'views/pe_payroll_config_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'post_init_hook': '_post_install_hook',
    'license': 'OPL-1',
}
