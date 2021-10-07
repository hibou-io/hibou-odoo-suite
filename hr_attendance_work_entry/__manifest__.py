{
    'name': 'Attendance Work Entry Type',
    'description': 'Set work types on attendance records.',
    'version': '15.0.1.0.0',
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
        'views/work_entry_views.xml',
    ],
    'demo': [
        'data/hr_attendance_work_entry_demo.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'hr_attendance_work_entry/static/src/xml/hr_attendance.xml',
        ],
        'web.assets_backend': [
            'hr_attendance_work_entry/static/src/js/kiosk_confirm.js',
            'hr_attendance_work_entry/static/src/js/my_attendances.js',
            'hr_attendance_work_entry/static/src/scss/hr_attendances.scss',
        ],
    },
    'pre_init_hook': 'attn_payroll_pre_init_hook',
}
