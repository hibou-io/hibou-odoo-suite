{
    'name': 'Signifyd Connector',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '15.0.1.1.0',
    'category': 'Sale',
    'description': """
Automate Order Fraud Detection with the Signifyd API.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'delivery',
        'hibou_professional',
        'stock',
        'website_sale',
        'website_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/payment_views.xml',
        'views/sale_views.xml',
        'views/signifyd_views.xml',
        'views/stock_views.xml',
        'views/web_assets.xml',
        'views/website_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}
