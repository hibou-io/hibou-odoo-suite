{
    'name': 'Timesheet Invoice',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Adds timesheet descriptions onto the invoice report/PDF.
    """,
    'depends': [
        'sale_timesheet',
    ],
    'data': [
        'invoice_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
