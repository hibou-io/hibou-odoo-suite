# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)


class WalmartStockPicking(models.Model):
    _name = 'walmart.stock.picking'
    _inherit = 'walmart.binding'
    _inherits = {'stock.picking': 'odoo_id'}
    _description = 'Walmart Delivery Order'

    odoo_id = fields.Many2one(comodel_name='stock.picking',
                              string='Stock Picking',
                              required=True,
                              ondelete='cascade')
    walmart_order_id = fields.Many2one(comodel_name='walmart.sale.order',
                                       string='Walmart Sale Order',
                                       ondelete='set null')

    @job(default_channel='root.walmart')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def export_picking_done(self):
        """ Export a complete or partial delivery order. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    walmart_bind_ids = fields.One2many(
        comodel_name='walmart.stock.picking',
        inverse_name='odoo_id',
        string="Walmart Bindings",
    )

class StockPickingAdapter(Component):
    _name = 'walmart.stock.picking.adapter'
    _inherit = 'walmart.adapter'
    _apply_on = 'walmart.stock.picking'

    def create(self, id, lines):
        api_instance = self.api_instance
        _logger.info('BEFORE SHIPPING %s list: %s' % (str(id), str(lines)))
        record = api_instance.orders.create_shipment(id, lines)
        _logger.info('AFTER SHIPPING RECORD: ' + str(record))
        if 'order' in record:
            return record['order']
        raise RetryableJobError('Shipping Order %s did not return an order response. (lines: %s)' % (str(id), str(lines)))


class WalmartBindingStockPickingListener(Component):
    _name = 'walmart.binding.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['walmart.stock.picking']

    def on_record_create(self, record, fields=None):
        record.with_delay().export_picking_done()


class WalmartStockPickingListener(Component):
    _name = 'walmart.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_picking_dropship_done(self, record, picking_method):
        return self.on_picking_out_done(record, picking_method)

    def on_picking_out_done(self, record, picking_method):
        """
        Create a ``walmart.stock.picking`` record. This record will then
        be exported to Walmart.

        :param picking_method: picking_method, can be 'complete' or 'partial'
        :type picking_method: str
        """
        sale = record.sale_id
        if not sale:
            return
        for walmart_sale in sale.walmart_bind_ids:
            self.env['walmart.stock.picking'].create({
                'backend_id': walmart_sale.backend_id.id,
                'odoo_id': record.id,
                'walmart_order_id': walmart_sale.id,
            })
