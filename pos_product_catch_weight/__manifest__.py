# Copyright 2018 Tecnativa S.L. - David Vidal
# ^^^ For OCA `pos_lot_selection`
# Copyright 2018 Hibou Corp. - Jared Kipe
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'POS Catch Weight',
    'version': '11.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Hibou Corp., '
              'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/pos',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale',
        'product_catch_weight',
    ],
    'data': [
        'templates/assets.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
    'application': False,
    'installable': True,
}
