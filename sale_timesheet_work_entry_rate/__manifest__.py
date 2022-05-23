# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Timesheet Billing Rate',
    'version': '15.0.1.1.0',
    'category': 'Sale',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        'hibou_professional',
        'hr_timesheet_work_entry',
        'timesheet_invoice',
        'sale_timesheet',
    ],
    'data': [
        'views/account_templates.xml',
        'views/timesheet_views.xml',
        'views/work_entry_views.xml',
    ],
    'demo': [
        'data/hr_timesheet_work_entry_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
 }
