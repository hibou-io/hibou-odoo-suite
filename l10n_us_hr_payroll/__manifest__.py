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
        'data/state/ak_alaska.xml',
        'data/state/al_alabama.xml',
        'data/state/ar_arkansas.xml',
        'data/state/az_arizona.xml',
        'data/state/ct_connecticut.xml',
        'data/state/fl_florida.xml',
        'data/state/ga_georgia.xml',
        'data/state/il_illinois.xml',
        'data/state/mi_michigan.xml',
        'data/state/mn_minnesota.xml',
        'data/state/mo_missouri.xml',
        'data/state/ms_mississippi.xml',
        'data/state/mt_montana.xml',
        'data/state/nc_northcarolina.xml',
        'data/state/nj_newjersey.xml',
        'data/state/oh_ohio.xml',
        'data/state/pa_pennsylvania.xml',
        'data/state/tx_texas.xml',
        'data/state/va_virginia.xml',
        'data/state/wa_washington.xml',
        'views/hr_contract_views.xml',
        'views/us_payroll_config_views.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'license': 'OPL-1',
}
