{
    'name': 'Payment Analytic',
    'version': '11.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Accounting',
    'summary': 'Record Analytic Account on Payment',
    'description': """
Record Analytic Account on Payment
""",
    'website': 'https://hibou.io/',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
