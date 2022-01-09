{
    'name': 'Timesheet Work Entry Type',
    'description': 'Set work types on timesheet records.',
    'version': '15.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'project',
        'hr_timesheet',
        'hr_work_entry',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_timesheet_work_entry_data.xml',
        'views/timesheet_views.xml',
        'views/work_entry_views.xml',
    ],
    'demo': [
        'data/hr_timesheet_work_entry_demo.xml',
    ],
    'pre_init_hook': 'ts_work_type_pre_init_hook',
}
