# © 2021 Hibou Corp.

from odoo import api, models, fields


class AmazonBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All of the models used as bindings between Amazon and Odoo
    (``amazon.sale.order``) should ``_inherit`` from it.
    """
    _name = 'amazon.binding'
    _inherit = 'external.binding'
    _description = 'Amazon Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='amazon.backend',
        string='Amazon Backend',
        required=True,
        ondelete='restrict',
    )
    external_id = fields.Char(string='ID in Amazon')

    _sql_constraints = [
        ('Amazon_uniq', 'unique(backend_id, external_id)', 'A binding already exists for this Amazon ID.'),
    ]

    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Amazon """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Amazon record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)
