# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Timesheets on Payslips',
    'description': 'Get Timesheet hours onto Employee Payslips.',
    'version': '15.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'OPL-1',
    'category': 'Human Resources',
    'data': [
        'data/hr_payroll_timesheet_data.xml',
        'views/hr_contract_view.xml',
        'views/hr_payslip_views.xml',
        'views/timesheet_views.xml',
    ],
    'demo': [
        'data/hr_payroll_timesheet_demo.xml',
    ],
    'depends': [
        'hr_payroll_hibou',
        'hr_timesheet_work_entry',
        'hr_payroll_overtime',
        'hibou_professional',
    ],
    'pre_init_hook': 'ts_payroll_pre_init_hook',
}
