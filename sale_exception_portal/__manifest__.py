{
    'name': 'Sale Exception Portal',
    'summary': 'Display sale exceptions on customer portal',
    'version': '13.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Sale',
    'license': 'AGPL-3',
    'website': "https://hibou.io",
    'description': """
Display sale exceptions on customer portal and prevent further action
""",
    'depends': [
        'sale_exception',
    ],
    'demo': [],
    'data': [
        'views/sale_portal_templates.xml',
        'views/sale_views.xml',
    ],
    'auto_install': False,
    'installable': True,
}
