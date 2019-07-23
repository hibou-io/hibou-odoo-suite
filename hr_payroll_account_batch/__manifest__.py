{
    'name': 'Payslip Batch Date',
    'description': """
Set the Accounting Date on a Payslip Batch.

Additionally, changes to the Salary Journal and Date Account on the batch itself 
will propagate to any draft payslip already existing on the batch.
""",
    'version': '12.0.1.0.0',
    'website': 'https://hibou.io/',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_payroll_account',
    ],
    'data': [
        'views/payroll_views.xml',
    ],
}
