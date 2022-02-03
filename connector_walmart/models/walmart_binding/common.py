# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class WalmartBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All of the models used as bindings between Walmart and Odoo
    (``walmart.sale.order``) should ``_inherit`` from it.
    """
    _name = 'walmart.binding'
    _inherit = 'external.binding'
    _description = 'Walmart Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='walmart.backend',
        string='Walmart Backend',
        required=True,
        ondelete='restrict',
    )
    external_id = fields.Char(string='ID in Walmart')

    _sql_constraints = [
        ('walmart_uniq', 'unique(backend_id, external_id)', 'A binding already exists for this Walmart ID.'),
    ]

    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Walmart """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Walmart record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)
