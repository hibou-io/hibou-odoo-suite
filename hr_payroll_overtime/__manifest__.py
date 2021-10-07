{
    'name': 'Payroll Overtime',
    'description': 'Provide mechanisms to calculate overtime.',
    'version': '15.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'security/ir.model.access.csv',
        'data/overtime_data.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_work_entry_views.xml',
        'views/resource_calendar_views.xml',
    ],
    'depends': [
        'hr_payroll_hibou',
        'hr_work_entry',
        'hr_work_entry_contract_enterprise',  # only for menu!
    ],
}
