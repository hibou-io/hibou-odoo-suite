{
    'name': 'Elavon Payment Services',
    'version': '12.0.1.0.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Credit card support for Point Of Sale',
    'description': """
Allow credit card POS payments
==============================

This module allows customers to pay for their orders with credit cards. 
The transactions are processed by Elavon. 
An Elavon merchant account is necessary. It allows the following:

* Fast payment by just swiping a credit card while on the payment screen
* Combining of cash payments and credit card payments
* Cashback
* Supported cards: Visa, MasterCard, American Express, Discover
    """,
    'depends': [
        'web',
        'barcodes',
        'pos_sale',
    ],
    'website': 'https://hibou.io',
    'data': [
        'data/pos_elavon_data.xml',
        'security/ir.model.access.csv',
        'views/pos_elavon_templates.xml',
        'views/pos_elavon_views.xml',
        'views/pos_config_setting_views.xml',
    ],
    'demo': [
        'data/pos_elavon_demo.xml',
    ],
    'qweb': [
        'static/src/xml/pos_elavon.xml',
    ],
    'installable': True,
    'auto_install': False,
}
