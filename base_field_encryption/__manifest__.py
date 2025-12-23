# -*- coding: utf-8 -*-
# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.
{
    'name': "Encryption Fields",
    'summary': """Implementation of encrypt fields.""",
    'description': """
The purpose of this module is to implement "encrypt" fields, i.e., fields
that are mostly null. This implementation circumvents the PostgreSQL
limitation on the number of columns in a table. The values of all encrypt
fields are stored in a "encryption" field in the form of a Encryption.
    """,
    'category': 'Hidden',
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'version': '19.0.1.0.0',
    'depends': ['base', 'sale'],
    'data': [],
    'license': 'LGPL-3',
    "external_dependencies": {"python": ["cryptography"]},
}
