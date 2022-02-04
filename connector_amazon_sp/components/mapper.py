# © 2021 Hibou Corp.

from odoo.addons.component.core import AbstractComponent


class AmazonImportMapper(AbstractComponent):
    _name = 'amazon.import.mapper'
    _inherit = ['base.amazon.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class AmazonExportMapper(AbstractComponent):
    _name = 'amazon.export.mapper'
    _inherit = ['base.amazon.connector', 'base.export.mapper']
    _usage = 'export.mapper'


def normalize_datetime(field):
    def modifier(self, record, to_attr):
        val = record.get(field, '')
        val = val.replace('T', ' ').replace('Z', '')
        return val
    return modifier
