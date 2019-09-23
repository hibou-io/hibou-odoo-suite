{
    'name': 'Partner Shipping Accounts',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Stock',
    'sequence': 95,
    'summary': 'Record shipping account numbers on partners.',
    'description': """
Record shipping account numbers on partners.

* Customer Shipping Account Model
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'delivery',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/delivery_views.xml',
    ],
    'installable': True,
    'application': False,
}
