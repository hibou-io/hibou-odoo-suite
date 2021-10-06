# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

{
    'name': 'Hibou Professional',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Tools',
    'depends': ['mail'],
    'version': '15.0.1.0.0',
    'description': """
Hibou Professional Support and Billing
======================================

    """,
    'website': 'https://hibou.io/',
    'data': [
    ],
    'assets': {
        'web.assets_qweb': [
            'hibou_professional/static/src/xml/templates.xml',
        ],
        'web.assets_backend': [
            'hibou_professional/static/src/css/web.css',
            'hibou_professional/static/src/js/core.js',
        ],
    },
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
