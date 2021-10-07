# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Attendance on Payslips',
    'description': 'Get Attendence numbers onto Employee Payslips.',
    'version': '15.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'OPL-1',
    'category': 'Human Resources',
    'data': [
        'data/hr_payroll_attendance_data.xml',
        'views/hr_attendance_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'depends': [
        'hr_payroll_hibou',
        'hr_attendance_work_entry',
        'hr_payroll_overtime',
        'hibou_professional',
    ],
    'pre_init_hook': 'attn_payroll_pre_init_hook',
}
