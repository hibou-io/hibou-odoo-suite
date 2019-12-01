# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class OpencartBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All of the models used as bindings between Opencart and Odoo
    (``opencart.sale.order``) should ``_inherit`` from it.
    """
    _name = 'opencart.binding'
    _inherit = 'external.binding'
    _description = 'Opencart Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='opencart.backend',
        string='Opencart Backend',
        required=True,
        ondelete='restrict',
    )
    external_id = fields.Char(string='ID in Opencart')

    _sql_constraints = [
        ('opencart_uniq', 'unique(backend_id, external_id)', 'A binding already exists for this Opencart ID.'),
    ]

    @job(default_channel='root.opencart')
    @related_action(action='related_action_opencart_link')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Opencart """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.opencart')
    @related_action(action='related_action_opencart_link')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Opencart record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)
