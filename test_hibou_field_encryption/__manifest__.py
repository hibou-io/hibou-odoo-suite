{
    'name': "Encryption Fields Tests",
    'summary': """Test models for hibou_field_encryption.""",
    'description': """
    Test-only models for the "encrypt" field implementation.

    These live in their own module rather than being built at runtime inside
    setUpClass(). Odoo 18 requires an encrypt field's storage attribute to be
    present on the model's Python class, and a model built at runtime trips the
    test framework's "Found unexpected attributes" check when the module sets
    it. Declaring the models normally avoids the registry surgery entirely.

    It also lets the suite cover an _inherits parent/child pair with a custom
    named blob, which is the shape real deployments use and the one most likely
    to break.
    """,
    'category': 'Hidden/Tests',
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'version': '18.0.1.0.0',
    'depends': ['hibou_field_encryption'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
