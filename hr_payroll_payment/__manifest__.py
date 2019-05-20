{
    'name': 'Payroll Payments',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '12.0.1.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Register payments for Payroll Payslips',
    'description': """
Adds the ability to register a payment on a payslip.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_payroll_account', 'payment'],
    'data': [
        'hr_payroll_register_payment.xml',
    ],
    'installable': True,
    'application': False,
}
