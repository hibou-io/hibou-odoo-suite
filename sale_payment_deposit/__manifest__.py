{
    'name': 'Sale Payment Deposit',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Sales',
    'version': '13.0.1.0.0',
    'description':
        """
Sale Deposits
=============

Automates the creation of 'Deposit' invoices and payments.  For example, someone confirming 
a sale with "50% Deposit, 50% on Delivery" payment terms, will pay the 
50% deposit payment up front instead of the entire order.
        """,
    'depends': [
        'sale',
        'payment',
    ],
    'auto_install': False,
    'data': [
        'views/account_views.xml',
        'views/sale_portal_templates.xml',
    ],
}
