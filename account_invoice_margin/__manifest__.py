{
    'name': 'Invoice Margin',
    'version': '17.0.1.1.0',
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
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
