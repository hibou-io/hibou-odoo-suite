{
    'name': 'Workers\' Compensation Class',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr_contract'],
    'version': '12.0.1.0.0',
    'description': """
Workers' Compensation Class
===========================

Provides a model to keep track of Workers' Comp. Class Codes and Rates.
    """,

    'auto_install': False,
    'website': 'https://hibou.io/',
    'data':[
        'ir.model.access.csv',
        'contract_views.xml',
    ],
    'installable': True
}
