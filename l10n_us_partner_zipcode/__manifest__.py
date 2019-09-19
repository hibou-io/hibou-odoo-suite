{
    'name': 'US ZIP Code to City/State',
    'summary': 'Determines the City and State from a provided ZIP code.',
    'version': '12.0.1.0.0',
    'author': "Hibou Corp.",
    'category': 'Localization',
    'license': 'AGPL-3',
    'complexity': 'easy',
    'images': [],
    'website': "https://hibou.io",
    'description': """
US ZIP Code to City/State
=========================

Determines the City and State from a provided ZIP code. Requires the `uszipcode` python package.

Does not require `base_geolocalize`, but will fill the related fields if possible.


Contributors
------------

* Jared Kipe <jared@hibou.io>

""",
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': ['uszipcode']
    },
    'demo': [],
    'data': [
    ],
    'auto_install': False,
    'installable': True,
}
