# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Manufaturing Order Exception',
    'version': '15.0.1.0.0',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': 'Custom exceptions on Manufacturing Orders',
    'description': """
Custom exceptions on journal entries
""",
    'website': 'https://hibou.io/',
    'depends': [
        'base_exception_user',
        'mrp',
    ],
    'data': [
        # 'demo/mrp_production_exception.xml',
        # 'security/ir.model.access.csv',
        # 'views/account_move_views.xml',
        # 'wizard/account_move_exception_confirm_views.xml',
    ],
    'demo': [
        'demo/account_exception_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
