# -*- coding: utf-8 -*-

{
    'name': 'Timesheets on Payslips',
    'description': 'Get Timesheet and Attendence numbers onto Employee Payslips.',
    'version': '1.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'hr_contract_view.xml',
    ],
    'depends': [
        'hr_payroll',
        'hr_timesheet_sheet',
    ],
}
