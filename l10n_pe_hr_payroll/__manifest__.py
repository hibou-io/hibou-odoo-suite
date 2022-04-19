# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Peru - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.2022.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll',
        'hr_contract_reports',
        'hibou_professional',
    ],
    'description': """
Peru - Payroll Rules.
=====================

    """,

    'data': [
        'data/base.xml',
        'data/integration_rules.xml',
        'data/afp_rules.xml',
        'data/er_rules.xml',
        # 'views/hr_contract_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'post_init_hook': '_post_install_hook',
    'license': 'OPL-1',
}
