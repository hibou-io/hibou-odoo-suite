{
    'name': 'DHL Partner Shipping Accounts',
    'author': 'Hibou Corp.',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 95,
    'summary': 'DHL Partner Shipping Accounts',
    'description': """
DHL Partner Shipping Accounts
===============================
This module adds DHL to delivery type selection dropdown on the Partner Shipping Account model.
Additionally, it validates entered DHL account numbers are the correct length.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'delivery_partner',
    ],
    'data': [
    ],
    'installable': True,
    'application': False,
}
