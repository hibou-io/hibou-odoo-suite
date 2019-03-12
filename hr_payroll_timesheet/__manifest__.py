{
    'name': 'Timesheets on Payslips',
    'description': 'Get Timesheet hours onto Employee Payslips.',
    'version': '12.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'views/hr_contract_view.xml',
    ],
    'depends': [
        'hr_payroll',
        'hr_timesheet',
    ],
}
