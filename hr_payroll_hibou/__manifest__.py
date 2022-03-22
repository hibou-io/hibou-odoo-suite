# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '15.0.2.1.0',
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

2.1.0 : fixes precision error in upstream by changing `normal_wage` field from Integer to Float
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/payroll_views.xml',
        'views/res_config_settings_views.xml',
        'views/update_views.xml',
    ],
    'demo': [
    ],
    'auto_install': True,
    'license': 'OPL-1',
}
