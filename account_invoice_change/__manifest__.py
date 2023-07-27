{
    'name': 'Account Invoice Change',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Accounting',
    'sequence': 95,
    'summary': 'Technical foundation for changing invoices.',
    'description': """
Technical foundation for changing invoices.

Creates wizard and permissions for making invoice changes that can be 
handled by other individual modules.

This module implements, as examples, how to change the Salesperson and Date fields.

Abstractly, individual 'changes' should come from specific 'fields' or capability 
modules that handle the consequences of changing that field in whatever state the 
the invoice is currently in.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'account',
    ],
    'data': [
        'data/server_actions.xml',
        'wizard/invoice_change_views.xml',
    ],
    'installable': True,
    'application': False,
}
