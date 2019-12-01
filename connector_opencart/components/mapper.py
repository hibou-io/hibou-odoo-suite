# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class OpencartImportMapper(AbstractComponent):
    _name = 'opencart.import.mapper'
    _inherit = ['base.opencart.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class OpencartExportMapper(AbstractComponent):
    _name = 'opencart.export.mapper'
    _inherit = ['base.opencart.connector', 'base.export.mapper']
    _usage = 'export.mapper'
