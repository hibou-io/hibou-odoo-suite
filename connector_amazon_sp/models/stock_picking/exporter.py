# © 2021 Hibou Corp.

from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import NothingToDoJob


class AmazonPickingExporter(Component):
    _name = 'amazon.stock.picking.exporter'
    _inherit = 'amazon.exporter'
    _apply_on = ['amazon.stock.picking']

    def _get_tracking(self, binding):
        return binding.carrier_tracking_ref or ''

    def _get_carrier_code(self, binding):
        return binding.carrier_id.amazon_sp_carrier_code or 'Other'

    def _get_carrier_name(self, binding):
        return binding.carrier_id.amazon_sp_carrier_name or binding.carrier_id.name or 'Other'

    def _get_shipping_method(self, binding):
        return binding.carrier_id.amazon_sp_shipping_method or 'Standard'

    def run(self, binding):
        """
        Export the picking to Amazon
        :param binding: amazon.stock.picking
        :return:
        """
        if binding.external_id:
            return 'Already exported'

        tracking = self._get_tracking(binding)
        if not tracking:
            raise NothingToDoJob('Cancelled: the delivery order does not contain tracking.')
        carrier_code = self._get_carrier_code(binding)
        carrier_name = self._get_carrier_name(binding)
        shipping_method = self._get_shipping_method(binding)
        _res = self.backend_adapter.create(binding, carrier_code, carrier_name, shipping_method, tracking)
        # Note we essentially bind to our own ID because we just need to notify Amazon
        self.binder.bind(str(binding.odoo_id), binding)
