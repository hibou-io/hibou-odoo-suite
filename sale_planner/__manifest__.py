{
    'name': 'Sale Order Planner',
    'summary': 'Plans order dates and warehouses.',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Sale',
    'license': 'AGPL-3',
    'complexity': 'expert',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Sale Order Planner
==================

Plans sales order dates based on available warehouses and shipping methods.

Adds shipping calendar to warehouse to plan delivery orders based on availability 
of the warehouse or warehouse staff.

Adds shipping calendar to individual shipping methods to estimate delivery based 
on the specific method's characteristics. (e.g. Do they deliver on Saturday?)


""",
    'depends': [
        'sale_sourced_by_line',
        'base_geolocalize',
        'delivery',
        'resource',
        'stock',
    ],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'wizard/order_planner_views.xml',
        'views/sale.xml',
        'views/stock.xml',
        'views/delivery.xml',
        'views/product.xml',
    ],
    'auto_install': False,
    'installable': True,
}
