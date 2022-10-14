{
    'name': 'Forte Payment Acquirer',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Forte Implementation',
    'version': '15.0.1.0.0',
    'description': """Forte Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
