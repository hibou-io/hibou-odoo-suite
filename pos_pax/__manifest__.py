# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'POS PAX Terminal Credit Card',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'PAX Terminal Credit card support for Point Of Sale',
    'description': """
Allow credit card POS payments
==============================

This module allows customers to pay for their orders with credit cards. 
The transactions are processed on the PAX Terminal (no credit credit card 
information through Odoo itself). 

Depending on Device and processor support, this integration can handle:

* Magnetic swiped cards
* EMV chip cards
* Contactless (including Apple Pay, Samsung Pay, Google Pay)

    """,
    'depends': [
        'web',
        'pos_sale',
        'hibou_professional',
    ],
    'website': 'https://hibou.io',
    'data': [
        'views/pos_config_setting_views.xml',
        'views/pos_pax_templates.xml',
        'views/pos_pax_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
        'static/src/xml/pos_pax.xml',
    ],
    'installable': True,
    'auto_install': False,
}
