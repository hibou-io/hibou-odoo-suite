{
    'name': 'Product Variant Always on SO',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '13.0.1.0.0',
    'description':
        """
Product Variant Always on SO
============================

The default limit in Odoo to 'always create variants' is 1000, but if you have a product 
that needs to use 'always create variants' attributes AND you have too many attributes, 
you may wish to have it behave as if it has attributes that 
        """,
    'depends': [
        'sale',
    ],
    'auto_install': False,
    'data': [
        'views/product_views.xml',
    ],
}
