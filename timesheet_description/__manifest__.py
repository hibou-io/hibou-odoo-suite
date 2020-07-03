{
    'name': 'Timesheet Description',
    'version': '13.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Tools',
    'complexity': 'easy',
    'description': """
Timesheet entries will be made in a form view, allowing the end user to enter more descriptive timesheet entries.

Optionally, allows you to display your timesheet entries in markdown on the front end of the website.
    """,
    'depends': [
        'project',
        'hr_timesheet',
    ],
    'data': [
        'views/project_templates.xml',
        'views/timesheet_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
