{
    'name': 'Reorder Rules per Warehouse',
    'version': '12.0.1.0.0',
    'category': 'Warehouse',
    'depends': [
        'stock',
    ],
    'description': """
Extends `stock.scheduler.compute` wizard to allow running on demand per-warehouse.

""",
    'author': "Hibou Corp.",
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'data': [
        'wizard/stock_scheduler_compute_views.xml',
    ],
    'installable': True,
    'application': False,
}
