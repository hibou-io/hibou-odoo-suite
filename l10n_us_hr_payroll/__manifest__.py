{
    'name': 'USA - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Localization',
    'depends': ['hr_payroll', 'hr_payroll_rate'],
    'version': '12.0.2020.1.0',
    'description': """
USA Payroll Rules.
==================

    * Contract W4 Filing Status & Allowances
    * FICA Social Security (with wages cap)
    * FICA Medicare
    * FICA Additioal Medicare Wages & Tax
    * FUTA Federal Unemployment (with wages cap)
    * Federal Income Tax Withholdings based on W4 values
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
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
        'data/state/ca_california.xml',
        'data/state/ct_connecticut.xml',
        'data/state/fl_florida.xml',
        'data/state/ga_georgia.xml',
        'data/state/hi_hawaii.xml',
        'data/state/id_idaho.xml',
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
        'data/final.xml',
        'views/hr_contract_views.xml',
        'views/us_payroll_config_views.xml',
    ],
    'installable': True,
    'license': 'OPL-1',
}
