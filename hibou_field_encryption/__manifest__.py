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
      - **file**: keys from a file on disk, so any secret manager can supply them
        (mounted Kubernetes secret, CSI driver, Vault Agent template, SOPS).
      - **gcp_secret_manager**: keys from Google Cloud Secret Manager with
        automatic version-to-keyring mapping.
    - Externally managed providers (file, GCP) are polled: a new key version is
      detected, published to every worker, and re-encrypted without a restart.
    - Single-key config (backward compatible): ``REC_ENCRYPTION_KEY=<key>``
    - Multi-key config: ``REC_ENCRYPTION_KEY=0:<key0>,1:<key1>,2:<key2>``
      where the highest version is the current encryption key.
    - Encrypted blobs are tagged with the key version that produced them.
    - Rotation is automatic: add a key version, restart, and old data is
      re-encrypted to the current version before the instance serves requests.
      Opt out with ``REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT`` and rotate manually
      via ``env['base']._re_encrypt_now()``.
    - Hourly cron job catches up anything the startup pass missed.
    - ``find_encryption_columns()`` discovers every encrypted column by field type,
      and ``re_encrypt_all()`` rotates all of them; ``re_encrypt_table()`` remains
      available for a single table.
    - Migration helper ``migrate_fields_to_encryption()`` for converting plaintext columns into encrypted blobs.
    """,
    'category': 'Hidden',
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'version': '18.0.3.0.0',
    'depends': ['base'],
    'data': [
        'data/cron_data.xml',
    ],
    'license': 'LGPL-3',
    "external_dependencies": {"python": ["cryptography"]},
}
