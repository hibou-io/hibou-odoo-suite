# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Exception Rule User',
    'version': '15.0.1.0.0',
    'author': 'Hibou Corp.',
    'license': 'OPL-1',
    'category': 'Generic Modules',
    'summary': 'Allow users to ignore exceptions',
    'description': """
Allow users to ignore exceptions 
""",
    'website': 'https://hibou.io/',
    'depends': [
        'base_exception',
    ],
    'data': [
        'security/base_exception_security.xml',
        'views/base_exception_views.xml',
        'wizard/base_exception_confirm_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
