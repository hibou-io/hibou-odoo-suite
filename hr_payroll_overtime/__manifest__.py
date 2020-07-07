{
    'name': 'Payroll Overtime',
    'description': 'Provide mechanisms to calculate overtime.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'security/ir.model.access.csv',
        'data/overtime_data.xml',
        'views/hr_work_entry_views.xml',
        'views/resource_calendar_views.xml',
    ],
    'depends': [
        'hr_payroll',
        'hr_work_entry',
    ],
}
