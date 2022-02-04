# © 2021 Hibou Corp.

from base64 import b64encode

from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component

import logging
_logger = logging.getLogger(__name__)


class AmazonStockPicking(models.Model):
    _name = 'amazon.stock.picking'
    _inherit = 'amazon.binding'
    _inherits = {'stock.picking': 'odoo_id'}
    _description = 'Amazon Delivery Order'

    odoo_id = fields.Many2one(comodel_name='stock.picking',
                              string='Stock Picking',
                              required=True,
                              ondelete='cascade')
    amazon_order_id = fields.Many2one(comodel_name='amazon.sale.order',
                                      string='Amazon Sale Order',
                                      ondelete='set null')

    @job(default_channel='root.amazon')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def export_picking_done(self):
        """ Export a complete or partial delivery order. """
        self.ensure_one()
        self = self.sudo()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amazon_bind_ids = fields.One2many(
        comodel_name='amazon.stock.picking',
        inverse_name='odoo_id',
        string="Amazon Bindings",
    )

    def has_amazon_pii(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner or not partner.email:
            return False
        return partner.email.find('@marketplace.amazon.com') >= 0


class StockPickingAdapter(Component):
    _name = 'amazon.stock.picking.adapter'
    _inherit = 'amazon.adapter'
    _apply_on = 'amazon.stock.picking'

    def _api(self):
        return self.api_instance.feeds()

    def create(self, amazon_picking, carrier_code, carrier_name, shipping_method, tracking):
        amazon_order = amazon_picking.amazon_order_id
        # api_instance = self.api_instance
        # feeds_api = self._api()

        order_line_qty = self._process_picking_items(amazon_picking)
        feed_root, _message = self._order_fulfillment_feed(amazon_picking, amazon_order, order_line_qty, carrier_code, carrier_name, shipping_method, tracking)
        feed_data = self._feed_string(feed_root)

        feed = self.env['amazon.feed'].create({
            'backend_id': amazon_order.backend_id.id,
            'type': 'POST_ORDER_FULFILLMENT_DATA',
            'content_type': 'text/xml',
            'data': b64encode(feed_data),
            'amazon_stock_picking_id': amazon_picking.id,
        })

        feed.with_delay(priority=20).submit_feed()
        _logger.info('Feed for Amazon Order %s for tracking number %s created.' % (amazon_order.external_id, tracking))
        return True

    def _process_picking_items(self, amazon_picking):
        amazon_order_line_to_qty = {}
        amazon_so_lines = amazon_picking.move_lines.mapped('sale_line_id.amazon_bind_ids')
        for so_line in amazon_so_lines:
            stock_moves = amazon_picking.move_lines.filtered(lambda sm: sm.sale_line_id.amazon_bind_ids in so_line and sm.quantity_done)
            if stock_moves:
                amazon_order_line_to_qty[so_line.external_id] = sum(stock_moves.mapped('quantity_done'))
        return amazon_order_line_to_qty

    def _order_fulfillment_feed(self, amazon_picking, amazon_order, order_line_qty, carrier_code, carrier_name, shipping_method, tracking):
        root, message = self._feed('OrderFulfillment', amazon_order.backend_id)
        order_fulfillment = self.ElementTree.SubElement(message, 'OrderFulfillment')
        self.ElementTree.SubElement(order_fulfillment, 'AmazonOrderID').text = amazon_order.external_id
        self.ElementTree.SubElement(order_fulfillment, 'FulfillmentDate').text = fields.Datetime.from_string(amazon_picking.create_date).isoformat()
        fulfillment_data = self.ElementTree.SubElement(order_fulfillment, 'FulfillmentData')
        self.ElementTree.SubElement(fulfillment_data, 'CarrierCode').text = carrier_code
        self.ElementTree.SubElement(fulfillment_data, 'CarrierName').text = carrier_name
        self.ElementTree.SubElement(fulfillment_data, 'ShippingMethod').text = shipping_method
        self.ElementTree.SubElement(fulfillment_data, 'ShipperTrackingNumber').text = tracking
        for num, qty in order_line_qty.items():
            item = self.ElementTree.SubElement(order_fulfillment, 'Item')
            self.ElementTree.SubElement(item, 'AmazonOrderItemCode').text = num
            self.ElementTree.SubElement(item, 'Quantity').text = str(int(qty))  # always whole
        return root, message


class AmazonBindingStockPickingListener(Component):
    _name = 'amazon.binding.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['amazon.stock.picking']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=10).export_picking_done()


class AmazonStockPickingListener(Component):
    _name = 'amazon.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_picking_dropship_done(self, record, picking_method):
        return self.on_picking_out_done(record, picking_method)

    def on_picking_out_done(self, record, picking_method):
        """
        Create a ``amazon.stock.picking`` record. This record will then
        be exported to Amazon.

        :param picking_method: picking_method, can be 'complete' or 'partial'
        :type picking_method: str
        """
        sale = record.sale_id
        if not sale:
            return
        if record.carrier_id.delivery_type == 'amazon_sp_mfn':
            # buying postage through Amazon already marks it shipped.
            return
        for amazon_sale in sale.amazon_bind_ids:
            self.env['amazon.stock.picking'].sudo().create({
                'backend_id': amazon_sale.backend_id.id,
                'odoo_id': record.id,
                'amazon_order_id': amazon_sale.id,
            })
