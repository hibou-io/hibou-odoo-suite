{
    'name': 'Equipment Usage',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Keep track of usage on different types of equipment.',
    'description': """
Equipment Usage
===============

Keep track of usage on different types of equipment. Adds fields for usage on equipments 
and descriptive UOM on categories.

Create preventative maintenance requests based on usage.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'hr_maintenance',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}