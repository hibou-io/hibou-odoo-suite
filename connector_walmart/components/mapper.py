# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class WalmartImportMapper(AbstractComponent):
    _name = 'walmart.import.mapper'
    _inherit = ['base.walmart.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class WalmartExportMapper(AbstractComponent):
    _name = 'walmart.export.mapper'
    _inherit = ['base.walmart.connector', 'base.export.mapper']
    _usage = 'export.mapper'
