{
    'name': 'Website Payment Terms',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Sales',
    'version': '13.0.1.0.0',
    'description':
        """
Website Payment Terms
=====================

Allow customers to choose payment terms if order total meets a configured threshold.
        """,
    'depends': [
        'sale_payment_deposit',
        'website_sale',
        'website_sale_delivery',
    ],
    'auto_install': False,
    'data': [
        'views/account_views.xml',
        'views/res_config_views.xml',
        'views/web_assets.xml',
        'views/website_templates.xml',
        'views/website_views.xml',
    ],
}
