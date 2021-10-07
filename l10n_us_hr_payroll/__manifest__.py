# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'United States of America - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.2020.0.0',
    'category': 'Payroll Localization',
    'depends': [
        'hr_payroll',
        'hr_contract_reports',
    ],
    'description': """
United States of America - Payroll Rules.
=========================================

    """,

    'data': [
        'security/ir.model.access.csv',
        'data/base.xml',
        'data/integration_rules.xml',
        'data/federal/fed_940_futa_parameters.xml',
        'data/federal/fed_940_futa_rules.xml',
        'data/federal/fed_941_fica_parameters.xml',
        'data/federal/fed_941_fica_rules.xml',
        'data/federal/fed_941_fit_parameters.xml',
        'data/federal/fed_941_fit_rules.xml',
        'views/hr_contract_views.xml',
        'views/us_payroll_config_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'license': 'OPL-1',
}
