# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Payment Disperse',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'category': 'Accounting',
    'summary': 'Pay multiple invoices with one Payment',
    'description': """
Pay multiple invoices with one Payment, and manually disperse the amount per invoice. 
""",
    'website': 'https://hibou.io/',
    'depends': [
        'account',
    ],
    'data': [
        'wizard/register_payment_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
