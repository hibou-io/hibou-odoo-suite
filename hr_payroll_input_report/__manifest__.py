# -*- coding: utf-8 -*-

{
    'name': 'Payroll Input Report',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '11.0.0.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Adds "Worked Days" and "Other Inputs" to the payslip reports.',
    'description': """
Adds "Worked Days" and "Other Inputs" to the payslip reports.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_payroll'],
    'data': ['hr_payroll_input_report.xml'],
    'installable': True,
    'application': False,
}
