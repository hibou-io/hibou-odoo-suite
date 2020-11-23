{
    'name': 'Purchase by Sale History',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Purchases',
    'sequence': 95,
    'summary': 'Fill Purchase Orders by Sales History',
    'description': """
Adds wizard to Purchase Orders that will fill the purchase order with products based on sales history.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'sale_stock',
        'purchase',
    ],
    'data': [
        'wizard/purchase_by_sale_history_views.xml',
    ],
    'installable': True,
    'application': False,
}
