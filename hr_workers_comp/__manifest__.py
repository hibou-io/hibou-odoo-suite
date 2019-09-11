{
    'name': 'Workers\' Compensation Class',
    'author': 'Hibou Corp. <hello@hibou.io>',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'website': 'https://hibou.io/',
    'version': '13.0.1.0.0',
    'description': """
Workers' Compensation Class
===========================

Provides a model to keep track of Workers' Comp. Class Codes and Rates.
    """,
    'depends': [
        'hr_contract',
    ],
    'data':[
        'security/ir.model.access.csv',
        'views/contract_views.xml',
    ],
    'auto_install': False,
    'installable': True
}
