{
    'name': 'HR Expense Change',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.0',
    'category': 'Employees',
    'sequence': 95,
    'summary': 'Technical foundation for changing expenses.',
    'description': """
Technical foundation for changing expenses.

Creates wizard and permissions for making expense changes that can be 
handled by other individual modules.

This module implements, as examples, how to change the Date fields.

Abstractly, individual 'changes' should come from specific 'fields' or capability 
modules that handle the consequences of changing that field in whatever state the 
the invoice is currently in.

    """,
    'website': 'https://hibou.io/',
    'depends': [
        'hr_expense',
    ],
    'data': [
        'wizard/expense_change_views.xml',
    ],
    'installable': True,
    'application': False,
}
