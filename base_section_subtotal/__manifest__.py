{
    'name': 'Base Section Subtotal',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'depends': [
        'account',  # because 'section_and_note_fields' come from account
    ],
    'data': [
        'views/assets_backend.xml',
    ],
    'installable': True,
    'application': False,
 }
