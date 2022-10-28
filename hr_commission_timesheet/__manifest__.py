# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Timesheet Commissions',
    'description': 'Pay commission on billed timesheets.',
    'version': '16.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'depends': [
        'hr_commission',
        'sale_timesheet',
    ],
    'category': 'Timesheets',
    'data': [
        'views/contract_views.xml',
    ],
    'installable': True,
}
