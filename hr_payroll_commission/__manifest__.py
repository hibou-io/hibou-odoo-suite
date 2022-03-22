# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Commissions in Payslips',
    'author': 'Hibou Corp.',
    'version': '15.0.1.0.0',
    'license': 'OPL-1',
    'category': 'Accounting/Commissions',
    'sequence': 95,
    'summary': 'Reimburse Commissions in Payslips',
    'description': """
Reimburse Commissions in Payslips
    """,
    'depends': [
        'hr_commission',
        'hr_payroll_hibou',
    ],
    'data': [
        'views/hr_commission_views.xml',
        'views/hr_payslip_views.xml',
        'data/hr_payroll_commission_data.xml',
    ],
    'demo': [
        'data/hr_payroll_commission_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
