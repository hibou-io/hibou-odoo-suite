{
    'name': 'Sale Credit Limit',
    'summary': 'Uses credit limit on Partners to warn salespeople if they are over their limit.',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Sale',
    'license': 'AGPL-3',
    'complexity': 'expert',
    'images': [],
    'website': "https://hibou.io",
    'description': """
Uses credit limit on Partners to warn salespeople if they are over their limit.

When confirming a sale order, the current sale order total will be considered and a Sale Order Exception 
will be created if the total would put them over their credit limit.
""",
    'depends': [
        'sale',
        'account',
        'sale_exception',
    ],
    'demo': [],
    'data': [
        'data/sale_exceptions.xml',
        'views/partner_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
