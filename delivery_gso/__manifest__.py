{
    'name': 'Golden State Overnight (gso.com) Shipping',
    'summary': 'Send your shippings through gso.com and track them online.',
    'version': '11.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Golden State Overnight (gso.com) Shipping
=========================================

* Provides estimates on shipping costs through gso.com.
* Send your shippings through gso.com and allows tracking of packages.
""",
    'depends': [
        'delivery_hibou',
    ],
    'demo': [],
    'data': [
        'views/delivery_gso_view.xml',
    ],
    'auto_install': False,
    'installable': True,
}
