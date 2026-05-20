{
    'name': "Encryption Fields",
    'summary': """Implementation of encrypt fields.""",
    'description': """
    The purpose of this module is to implement "encrypt" fields.
    The values of all 'encrypt' fields are stored in a "Encryption" field.

    Features:
    - ``encrypt=True`` shorthand that automatically creates a conventional ``rec_encrypted`` Encryption field.
    - Encryption key can be provided via the Odoo config file or the ``REC_ENCRYPTION_KEY`` environment variable.
    - Migration helper ``migrate_fields_to_encryption()`` for converting plaintext columns into encrypted blobs.
    """,
    'category': 'Hidden',
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'version': '18.0.1.0.0',
    'depends': ['base'],
    'data': [],
    'license': 'LGPL-3',
    "external_dependencies": {"python": ["cryptography"]},
}
