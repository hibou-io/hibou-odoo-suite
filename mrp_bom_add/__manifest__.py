{
    'name': 'BoM Mass Add',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '13.0.1.1.0',
    'description':
        """
Bill of Materials Mass Component Adder
======================================

Helper to add all variants of a Product to a BoM filtered by the attributes on that product.
Adds a button under BoM components named "Add Bulk".  This lets you select a product template 
and add one BoM line for every variant of that product.

Optionally you can choose to only add the variants that could be selected by the attributes 
on the produced product itself.  You can also replace all of the lines for the slected product 
to allow you to quickly re-configure qty or operation for bulk products.
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
