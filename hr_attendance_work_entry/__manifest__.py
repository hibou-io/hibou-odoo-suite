{
    'name': 'Attendance Work Entry Type',
    'description': 'Set work types on attendance records.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'data/hr_attendance_work_entry_data.xml',
    ],
    'depends': [
        'hr_attendance',
        'hr_work_entry',
    ],
    'pre_init_hook': 'attn_payroll_pre_init_hook',
}
