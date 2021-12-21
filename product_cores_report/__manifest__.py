# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Product Core Reporting',
    'version': '15.0.1.0.0',
    'category': 'Account',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        'account_reports',
        'product_cores',
    ],
    'data': [
        'views/account_views.xml',
        'views/report_templates.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
 }
