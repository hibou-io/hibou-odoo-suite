# © 2021 Hibou Corp.

from odoo.addons.component.core import Component


class AmazonProductProductExporter(Component):
    _name = 'amazon.product.product.exporter'
    _inherit = 'amazon.exporter'
    _apply_on = ['amazon.product.product']
    _usage = 'amazon.product.product.exporter'

    def run(self, bindings):
        # TODO should exporter prepare feed data?
        self.backend_adapter.create(bindings)

    def run_inventory(self, bindings):
        # TODO should exporter prepare feed data?
        self.backend_adapter.create_inventory(bindings)

    def run_price(self, bindings):
        # TODO should exporter prepare feed data?
        self.backend_adapter.create_price(bindings)
