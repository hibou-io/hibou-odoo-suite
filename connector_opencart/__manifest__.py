# © 2019-2021 Hibou Corp.

{
    'name': 'Opencart Connector',
    'version': '16.0.1.0.0',
    'category': 'Connector',
    'depends': [
        'account',
        'product',
        'delivery',
        'sale_stock',
        'connector_ecommerce',
        'base_technical_user',
    ],
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io',
    'data': [
        'data/connector_opencart_data.xml',
        'security/ir.model.access.csv',
        'views/delivery_views.xml',
        'views/opencart_backend_views.xml',
        'views/opencart_product_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
}
