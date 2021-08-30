{
    'name': 'Timesheet Grid Work Entry',
    'description': 'bridge',
    'version': '14.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_timesheet_work_entry',
        'timesheet_grid',
    ],
    'data': [
        'views/timesheet_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
