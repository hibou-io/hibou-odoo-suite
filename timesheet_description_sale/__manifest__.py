{
    'name': 'Timesheet Description Sale',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Linker module to inject fields required by timesheets for sales.
    """,
    'depends': [
        'timesheet_description',
        'sale_timesheet',
    ],
    'data': [
        'views/timesheet_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
