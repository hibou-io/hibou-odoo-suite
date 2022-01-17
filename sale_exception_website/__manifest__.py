{
    'name': 'Sale Exception Website',
    'summary': 'Display sale exceptions on eCommerce site',
    'version': '15.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Sale',
    'license': 'AGPL-3',
    'website': "https://hibou.io",
    'description': """
Display sale exceptions on eCommerce site and prevent purchases
""",
    'depends': [
        'sale_exception_portal',
        'website_sale',
    ],
    'demo': [],
    'data': [
        'views/website_templates.xml',
    ],
    'auto_install': False,
    'installable': True,
}
