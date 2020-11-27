# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '14.0.1.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll',
        'hr_contract_reports',
        'hibou_professional',
    ],
    'description': """
Hibou Payroll
=============

Base module for fixing specific qwerks or assumptions in the way Payroll Odoo Enterprise Edition behaves.

    """,
    'data': [
        'views/hr_contract_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
    ],
    'auto_install': True,
    'license': 'OPL-1',
}
