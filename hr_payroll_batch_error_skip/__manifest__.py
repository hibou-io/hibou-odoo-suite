{
    'name': 'Payroll Batch Work Entry Errork SKIP',
    'description': 'This module bypasses a blocking error on payroll batch runs. '
                   'If your business does not depend on the stock functionality '
                   '(e.g. you use Timesheet and salary but not the stock work schedule '
                   'calculations), this will alleviate your blocking issues.',
    'version': '13.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'data': [
    ],
    'depends': [
        'hr_payroll',
    ],
}
