# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Walmart Connector',
    'version': '12.0.1.2.0',
    'category': 'Connector',
    'depends': [
        'account',
        'product',
        'delivery',
        'sale_stock',
        'connector_ecommerce',
    ],
    'author': "Hibou Corp.",
    'license': 'AGPL-3',
    'website': 'https://hibou.io',
    'data': [
        'views/walmart_backend_views.xml',
        'views/connector_walmart_menu.xml',
        'views/sale_order_views.xml',
        'views/account_views.xml',
        'views/delivery_views.xml',
        'security/ir.model.access.csv',
        'data/connector_walmart_data.xml',
    ],
    'installable': True,
    'application': False,
}
