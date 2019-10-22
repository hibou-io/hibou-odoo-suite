{
    'name': 'MRP Production Add Item',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Add Items to an existing Production',
    'description': """
This module allows a production order to add additional items that are not on the product's BoM.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'mrp',
    ],
    'data': [
        'wizard/additem_wizard_view.xml',
        'views/mrp_production.xml',
    ],
    'installable': True,
}
