{
    'name': 'Account Invoice Change - Analytic',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'sequence': 95,
    'summary': 'Change Analytic Account on Invoice.',
    'description': """
Adds fields and functionality to change the analytic account on all invoice lines 
and subsequent documents.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'account_invoice_change',
        'analytic',
    ],
    'data': [
        'wizard/invoice_change_views.xml',
    ],
    'installable': True,
    'application': False,
}
