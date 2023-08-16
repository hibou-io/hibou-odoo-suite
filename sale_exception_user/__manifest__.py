# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Sale Exception Rule User',
    'version': '16.0.1.0.0',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': 'Allow users to ignore sale exceptions',
    'description': """
Allow users to ignore sale exceptions 
""",
    'website': 'https://hibou.io/',
    'depends': [
        'base_exception_user',
        'sale_exception',
    ],
    'data': [
        'wizard/sale_exception_confirm_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
