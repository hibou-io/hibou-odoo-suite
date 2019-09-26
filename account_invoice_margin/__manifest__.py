{
    'name': 'Invoice Margin',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Accounting',
    'sequence': 95,
    'summary': 'Invoices include margin calculation.',
    'description': """
Invoices include margin calculation.
If the invoice line comes from a sale order line, the cost will come 
from the sale order line.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'account',
        'sale_margin',
    ],
    'data': [
        'views/account_invoice_views.xml',
    ],
    'installable': True,
    'application': False,
}
