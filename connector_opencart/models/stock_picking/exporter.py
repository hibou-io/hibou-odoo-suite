# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import NothingToDoJob


class OpencartPickingExporter(Component):
    _name = 'opencart.stock.picking.exporter'
    _inherit = 'opencart.exporter'
    _apply_on = ['opencart.stock.picking']

    def _get_id(self, binding):
        sale_binder = self.binder_for('opencart.sale.order')
        opencart_sale_id = sale_binder.to_external(binding.opencart_order_id)
        return opencart_sale_id

    def _get_tracking(self, binding):
        return binding.carrier_tracking_ref or ''

    def run(self, binding):
        """
        Export the picking to Opencart
        :param binding: opencart.stock.picking
        :return:
        """
        if binding.external_id:
            return 'Already exported'

        tracking = self._get_tracking(binding)
        if not tracking:
            raise NothingToDoJob('Cancelled: the delivery order does not contain tracking.')
        id = self._get_id(binding)
        _ = self.backend_adapter.create(id, tracking)
        # Cannot bind because shipments do not have ID's in Opencart
        #self.binder.bind(external_id, binding)
