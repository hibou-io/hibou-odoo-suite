{
    'name': 'Auth Admin',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Hidden',
    'version': '13.0.1.0.0',
    'description':
        """
Login as other user
===================

Provides a way for an authenticated user, with certain permissions, to login as a different user.
Can also create a URL that logs in as that user.

Out of the box, only allows you to generate a login for an 'External User', e.g. portal users.

*2017-11-15* New button to generate the login on the Portal User Wizard (Action on Contact)
        """,
    'depends': [
        'base',
        'website',
        'portal',
    ],
    'auto_install': False,
    'data': [
        'views/res_users.xml',
        'wizard/portal_wizard_views.xml',
    ],
}
