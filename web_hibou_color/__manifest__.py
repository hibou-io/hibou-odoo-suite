{
    'name': 'Web Hibou Color',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'description': """
Hibou Colors
============

This module modifies the web addon to provide alternative colors.
        """,
    'depends': [
        'web',
    ],
    'auto_install': True,
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'web_hibou_color/static/src/legacy/scss/primary_variables.scss'),
        ],
    },
    'license': 'LGPL-3',
}
