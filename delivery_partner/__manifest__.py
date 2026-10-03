{
    'name': 'Partner Shipping Accounts',
    'author': 'Hibou Corp.',
    'version': '20.0.1.0.0',
    'license': 'LGPL-3',
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
        'security/ir.access.csv',
        'views/delivery_views.xml',
    ],
    'installable': True,
    'application': False,
}
