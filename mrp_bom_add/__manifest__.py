{
    'name': 'BoM Mass Add',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '12.0.1.0.0',
    'description':
        """
Bill of Materials Mass Component Adder
======================================

Helper to add all variants of a Product to a BoM filtered by the attributes on that product.
Adds a button under BoM components named "Add Bulk".  This lets you configure a product
        """,
    'depends': [
        'mrp',
        'sale',
    ],
    'auto_install': False,
    'data': [
        'wizard/mrp_bom_add_views.xml',
    ],
}
