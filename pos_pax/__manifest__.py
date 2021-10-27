# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'POS PAX Terminal Credit Card',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '15.0.1.0.0',
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
        'pos_sale',
        'hibou_professional',
    ],
    'website': 'https://hibou.io',
    'data': [
        'views/pos_config_setting_views.xml',
        'views/pos_pax_views.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_qweb': [
            'pos_pax/static/src/xml/OrderReceipt.xml',
            'pos_pax/static/src/xml/PAXPaymentTransactionPopup.xml',
            'pos_pax/static/src/xml/PAXPaymentScreenPaymentLines.xml',
        ],
        'point_of_sale.assets': [
            'pos_pax/static/src/js/jquery_base64.js',
            'pos_pax/static/src/js/pax_device.js',
            'pos_pax/static/src/js/pos_pax.js',
            'pos_pax/static/src/js/PAXPaymentTransactionPopup.js',
            'pos_pax/static/src/js/PAXPaymentScreen.js',
            'pos_pax/static/src/js/PAXPaymentScreenPaymentLines.js',
            'pos_pax/static/src/css/pos_pax.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
