{
    'name': 'Payroll Rates',
    'description': 'Payroll Rates',
    'version': '12.0.1.0.1',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
        'security/ir.model.access.csv',
        'views/payroll_views.xml',
    ],
    'depends': [
        'hr_payroll',
    ],
}
