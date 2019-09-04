{
    'name': 'Stock Picklist',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'depends': [
        'stock_picking_batch',
    ],
    'description': """
Stock Picklist
==============

Adds a `Picklist` button to picking batches (waves) that provides a summary grouped by location 
and product for all of the pickings in the batch.
    """,
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'data': [
        'report/stock_picklist.xml',
        'views/stock_views.xml',
    ],
    'installable': True,
    'application': False,
}
