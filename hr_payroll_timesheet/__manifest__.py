{
    'name': 'Timesheets on Payslips',
    'description': 'Get Timesheet hours onto Employee Payslips.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'data/hr_payroll_timesheet_data.xml',
        'views/hr_contract_view.xml',
        'views/hr_payslip_views.xml',
    ],
    'depends': [
        'hr_payroll',
        'hr_timesheet',
        'hr_payroll_overtime',
    ],
    'pre_init_hook': 'ts_payroll_pre_init_hook',
}
