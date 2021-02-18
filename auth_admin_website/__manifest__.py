{
    'name': 'Auth Admin Website',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '13.0.1.0.0',
    'description':
        """
Login as other user
===================

Add support for multiple websites to Auth Admin
        """,
    'depends': [
        'auth_admin',
        'website',
    ],
    'auto_install': True,
    'data': [
        'wizard/portal_wizard_views.xml',
    ],
}
