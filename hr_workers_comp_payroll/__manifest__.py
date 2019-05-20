{
    'name': 'Workers\' Compensation Class - Payroll',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_payroll',
        'hr_workers_comp',
    ],
    'version': '12.0.1.0.0',
    'description': """
Workers' Compensation Class - Payroll
=====================================

Links Payslips with Contract's WC Codes.  Useful for reporting and grouping payslips.
Salary Rules can now make use of the Workers Comp code and rate.
    """,
    'auto_install': True,
    'website': 'https://hibou.io/',
    'data':[
        'payslip_views.xml',
    ],
    'installable': True
}
