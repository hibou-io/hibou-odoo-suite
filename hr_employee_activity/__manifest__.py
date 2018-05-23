{
    'name': 'HR Employee Activity',
    'version': '11.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'website': 'https://hibou.io/',
    'license': 'AGPL-3',
    'category': 'Employees',
    'complexity': 'easy',
    'description': """
This module adds activity to the `hr.employee` model.
    """,
    'depends': [
        'hr',
    ],
    'data': [
        'hr_employee_activity_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'category': 'Hidden',
}
