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
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'wizard/mrp_production_exception_confirm_views.xml',
    ],
    'demo': [
        'demo/mrp_production_exception.xml',
    ],
    'installable': True,
    'auto_install': False,
}
