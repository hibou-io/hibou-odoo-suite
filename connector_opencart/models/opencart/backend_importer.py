# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class MetadataBatchImporter(Component):
    """ Import the records directly, without delaying the jobs.

    Import the Opencart Stores

    They are imported directly because this is a rare and fast operation,
    and we don't really bother if it blocks the UI during this time.

    """

    _name = 'opencart.metadata.batch.importer'
    _inherit = 'opencart.direct.batch.importer'
    _apply_on = ['opencart.store']
