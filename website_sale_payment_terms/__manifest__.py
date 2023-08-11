{
    'name': 'Website Payment Terms',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'category': 'Sales',
    'version': '16.0.1.0.0',
    'description':
        """
Website Payment Terms
=====================

Allow customers to choose payment terms if order total meets a configured threshold.
        """,
    'depends': [
        'sale_payment_deposit',
        # 'website_sale',
        'website_sale_delivery',
    ],
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/res_config_views.xml',
        'views/website_templates.xml',
        'views/website_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/website_sale_payment_terms/static/src/js/payment_terms.js',
        ],
    },
}
