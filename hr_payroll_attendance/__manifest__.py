{
    'name': 'Attendance on Payslips',
    'description': 'Get Attendence numbers onto Employee Payslips.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'data/hr_payroll_attendance_data.xml',
        'views/hr_attendance_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'depends': [
        'hr_payroll',
        'hr_attendance',
        'hr_payroll_overtime',
    ],
    'pre_init_hook': 'attn_payroll_pre_init_hook',
}
