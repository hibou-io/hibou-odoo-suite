# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou Commissions',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'version': '13.0.1.0.1',
    'category': 'Accounting/Commissions',
    'license': 'OPL-1',
    'website': 'https://hibou.io/',
    'depends': [
        # 'account_invoice_margin',  # optional
        'hr_contract',
    ],
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/commission_views.xml',
        'views/hr_views.xml',
        'views/partner_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
 }
