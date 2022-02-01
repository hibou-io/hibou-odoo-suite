# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Sale Commissions',
    'description': 'Bridge module to add commission menus for sales users.',
    'version': '15.0.1.0.0',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'depends': [
        'hr_commission',
        'sale_management',
    ],
    'category': 'Tools',
    'data': [
        'views/commission_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
