{
    'name': "Encryption Fields",
    'summary': """Implementation of encrypt fields with versioned keyring.""",
    'description': """
    The purpose of this module is to implement "encrypt" fields.
    The values of all 'encrypt' fields are stored in a "Encryption" field.

    Features:
    - ``encrypt=True`` shorthand that automatically creates a conventional ``rec_encrypted`` Encryption field.
    - Versioned keyring supporting multiple Fernet keys for seamless rotation.
    - Pluggable key providers:
      - **config** (default): keys from Odoo config file or environment variables.
      - **gcp_secret_manager**: keys from Google Cloud Secret Manager with
        automatic version-to-keyring mapping.
    - Single-key config (backward compatible): ``REC_ENCRYPTION_KEY=<key>``
    - Multi-key config: ``REC_ENCRYPTION_KEY=0:<key0>,1:<key1>,2:<key2>``
      where the highest version is the current encryption key.
    - Encrypted blobs are tagged with the key version that produced them.
    - Daily cron job automatically re-encrypts old data to the current key version.
    - ``re_encrypt_table()`` helper for manual/immediate rotation.
    - Migration helper ``migrate_fields_to_encryption()`` for converting plaintext columns into encrypted blobs.
    """,
    'category': 'Hidden',
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'version': '18.0.2.0.0',
    'depends': ['base'],
    'data': [
        'data/cron_data.xml',
    ],
    'license': 'LGPL-3',
    "external_dependencies": {"python": ["cryptography"]},
}
