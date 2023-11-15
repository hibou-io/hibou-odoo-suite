{
    'name': 'UPS Partner Shipping Accounts',
    'author': 'Hibou Corp.',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Stock',
    'sequence': 95,
    'summary': 'UPS Partner Shipping Accounts',
    'description': """
UPS Partner Shipping Accounts
=============================
This module adds UPS to the delivery type selection dropdown on the Partner Shipping Account model.
Additionally, it adds a new required field UPS Account ZIP, as well as validation of entered UPS account number.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'delivery_partner',
    ],
    'data': [
        'views/delivery_views.xml',
    ],
    'installable': True,
    'application': False,
}
