{
    'name': 'Equipment Timesheets',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Human Resources',
    'summary': 'Record time on maintenance requests.',
    'description': """
Equipment Timesheets
====================

Adds Timesheets to Maintenance Requests to record time and labor costs.
""",
    'website': 'https://hibou.io/',
    'depends': [
        'maintenance_notebook',
        'hr_department_project',
        'hr_timesheet',
    ],
    'data': [
        'views/maintenance_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
