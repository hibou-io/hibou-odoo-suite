{
    'name': 'Purolator Shipping',
    'summary': 'Send your shippings through Purolator and track them online.',
    'version': '15.0.1.0.1',
    'author': "Hibou Corp.",
    'category': 'Warehouse',
    'license': 'OPL-1',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Purolator Shipping
==================

* Provides estimates on shipping costs.
* Send your shippings and track packages.
""",
    'depends': [
        'delivery_hibou',
    ],
    'demo': [
        'data/delivery_purolator_demo.xml',
    ],
    'data': [
        'data/delivery_purolator_data.xml',
        'views/delivery_purolator_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
