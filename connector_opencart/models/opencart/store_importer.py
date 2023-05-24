# © 2019-2021 Hibou Corp.

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class OpencartStoreImportMapper(Component):
    _name = 'opencart.store.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = 'opencart.store'

    direct = [
        ('config_name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class OpencartStoreImporter(Component):
    """ Import one Opencart Store """

    _name = 'opencart.store.importer'
    _inherit = 'opencart.importer'
    _apply_on = 'opencart.store'
