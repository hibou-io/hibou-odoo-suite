# © 2021 Hibou Corp.

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


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

    @job(default_channel='root.amazon')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Amazon """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.amazon')
    @related_action(action='related_action_unwrap_binding')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Amazon record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)

    # @job(default_channel='root.amazon')
    # @related_action(action='related_action_unwrap_binding')
    # @api.multi
    # def export_record(self, fields=None):
    #     """ Export a record on Amazon """
    #     self.ensure_one()
    #     with self.backend_id.work_on(self._name) as work:
    #         exporter = work.component(usage='record.exporter')
    #         return exporter.run(self, fields)
    #
    # @job(default_channel='root.amazon')
    # @related_action(action='related_action_amazon_link')
    # def export_delete_record(self, backend, external_id):
    #     """ Delete a record on Amazon """
    #     with backend.work_on(self._name) as work:
    #         deleter = work.component(usage='record.exporter.deleter')
    #         return deleter.run(external_id)
