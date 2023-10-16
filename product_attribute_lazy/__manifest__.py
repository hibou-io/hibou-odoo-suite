{
    'name': 'Product Attribute Lazy',
    'author': 'Hibou Corp.',
    'version': '16.0.1.0.0',
    'category': 'Product',
    'sequence': 95,
    'summary': 'Performance module to change behavior of attribute-product-template relationship.',
    'description': """
Performance module to change behavior of attribute-product-template relationship.

Adds scheduled action to reindex all attributes.

Adds scheduled action that will kill queries to this table, 
you can deactive if you're not having issues with long running table queries.

By default, a new pure SQL version of the index is created.  If you would like to use the slower ORM 
computation, set system config parameter `product_attribute_lazy.indexer_use_sql` to '0'.
    """,
    'website': 'https://hibou.io/',
    'depends': [
        'product',
    ],
    'data': [
        'data/product_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
