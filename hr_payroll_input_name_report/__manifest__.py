# -*- coding: utf-8 -*-

{
    'name': 'Payroll Input Name Report',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '11.0.0.0.0',
    'category': 'Human Resources',
    'sequence': 95,
    'summary': 'Improves slip reports by using your own Input\'s description',
    'description': """
If a Salary Rule\'s Code is identical to an Input's Code, then the input's description 
will appear on the payslip report where the rule is displayed.
    """,
    'website': 'https://hibou.io/',
    'depends': ['hr_payroll'],
    'data': ['hr_payroll_input_name_report.xml'],
    'installable': True,
    'application': False,
}
