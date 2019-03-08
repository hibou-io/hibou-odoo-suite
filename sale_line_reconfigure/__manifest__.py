{
    'name': 'Sale Line Reconfigure',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '12.0.1.0.0',
    'description':
        """
Sale Line Reconfigure
=====================

The product configurator allows for truely complex sale order lines, with potentially 
no-variant and custom attribute values.

This module allows you to create 'duplicate' sale order lines that start with all of
the attribute values from some other line.  This lets you treat existing SO lines as 
templates for the new additions. This lets you "re-configure" a line by a 
workflow in which you add a new line, then remove old line (or reduce its ordered quantity).
        """,
    'depends': [
        'sale',
        'account',
    ],
    'auto_install': False,
    'data': [
        'views/assets.xml',
        'views/product_views.xml',
        'views/sale_product_configurator_templates.xml',
    ],
}
