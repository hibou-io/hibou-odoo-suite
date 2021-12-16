# © 2019-2021 Hibou Corp.

from odoo import api, models, fields, _
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError


class OpencartStockPicking(models.Model):
    _name = 'opencart.stock.picking'
    _inherit = 'opencart.binding'
    _inherits = {'stock.picking': 'odoo_id'}
    _description = 'Opencart Delivery Order'

    odoo_id = fields.Many2one(comodel_name='stock.picking',
                              string='Stock Picking',
                              required=True,
                              ondelete='cascade')
    opencart_order_id = fields.Many2one(comodel_name='opencart.sale.order',
                                       string='Opencart Sale Order',
                                       ondelete='set null')

    def export_picking_done(self):
        """ Export a complete or partial delivery order. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    opencart_bind_ids = fields.One2many(
        comodel_name='opencart.stock.picking',
        inverse_name='odoo_id',
        string="Opencart Bindings",
    )


class StockPickingAdapter(Component):
    _name = 'opencart.stock.picking.adapter'
    _inherit = 'opencart.adapter'
    _apply_on = 'opencart.stock.picking'

    def create(self, id, tracking):
        api_instance = self.api_instance
        tracking_comment = _('Order shipped with tracking number: %s') % (tracking, )
        result = api_instance.orders.ship(id, tracking, tracking_comment)
        if 'success' in result:
            return result['success']
        raise RetryableJobError('Shipping Order %s did not return an order response. (tracking: %s) %s' % (
            str(id), str(tracking), str(result)))


class OpencartBindingStockPickingListener(Component):
    _name = 'opencart.binding.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['opencart.stock.picking']

    def on_record_create(self, record, fields=None):
        record.with_delay().export_picking_done()


class OpencartStockPickingListener(Component):
    _name = 'opencart.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_picking_dropship_done(self, record, picking_method):
        return self.on_picking_out_done(record, picking_method)

    def on_picking_out_done(self, record, picking_method):
        """
        Create a ``opencart.stock.picking`` record. This record will then
        be exported to Opencart.

        :param picking_method: picking_method, can be 'complete' or 'partial'
        :type picking_method: str
        """
        sale = record.sale_id
        if not sale:
            return
        for opencart_sale in sale.opencart_bind_ids:
            self.env['opencart.stock.picking'].create({
                'backend_id': opencart_sale.backend_id.id,
                'odoo_id': record.id,
                'opencart_order_id': opencart_sale.id,
            })
