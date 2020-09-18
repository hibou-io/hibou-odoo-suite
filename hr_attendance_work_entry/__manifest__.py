{
    'name': 'Attendance Work Entry Type',
    'description': 'Set work types on attendance records.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_attendance',
        'hr_work_entry',
    ],
    'data': [
        'data/hr_attendance_work_entry_data.xml',
        'views/attendance_views.xml',
        'views/employee_views.xml',
        'views/web_assets.xml',
        'views/work_entry_views.xml',
    ],
    'demo': [
        'data/hr_attendance_work_entry_demo.xml',
    ],
    'qweb': [
        'static/src/xml/hr_attendance.xml',
    ],
    'pre_init_hook': 'attn_payroll_pre_init_hook',
}
