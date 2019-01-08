{
    'name': 'Account Payment Electronic',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '12.0.1.0.0',
    'description':
        """
Register Electronic Payments
============================

Adds the payment token mechanism onto stock 'Register Payment' Wizard.
        """,
    'depends': [
        'payment',
    ],
    'auto_install': False,
    'data': [
        'views/account_views.xml',
    ],
}
