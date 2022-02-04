# © 2021 Hibou Corp.

import logging
from time import sleep

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError

from ...components.api.amazon import RequestRateError

SO_REQUEST_SLEEP_SECONDS = 30

_logger = logging.getLogger(__name__)

SO_IMPORT_RETRY_PATTERN = {
    1:  10 * 60,
    2:  30 * 60,
}


class AmazonSaleOrder(models.Model):
    _name = 'amazon.sale.order'
    _inherit = 'amazon.binding'
    _description = 'Amazon Sale Order'
    _inherits = {'sale.order': 'odoo_id'}
    _order = 'date_order desc, id desc'

    odoo_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    amazon_order_line_ids = fields.One2many(
        comodel_name='amazon.sale.order.line',
        inverse_name='amazon_order_id',
        string='Amazon Order Lines'
    )
    total_amount = fields.Float(
        string='Total amount',
        digits=dp.get_precision('Account')
    )
    # total_amount_tax = fields.Float(
    #     string='Total amount w. tax',
    #     digits=dp.get_precision('Account')
    # )
    # Ideally would be a selection, but there are/will be more codes we might
    # not be able to predict like 'Second US D2D Dom'
    # Standard, Expedited, Second US D2D Dom,
    fulfillment_channel = fields.Selection([
        ('AFN', 'Amazon'),
        ('MFN', 'Merchant'),
    ], string='Fulfillment Channel')
    ship_service_level = fields.Char(string='Shipping Service Level')
    ship_service_level_category = fields.Char(string='Shipping Service Level Category')
    marketplace = fields.Char(string='Marketplace')
    order_type = fields.Char(string='Order Type')
    is_business_order = fields.Boolean(string='Is Business Order')
    is_prime = fields.Boolean(string='Is Prime')
    is_global_express_enabled = fields.Boolean(string='Is Global Express')
    is_premium = fields.Boolean(string='Is Premium')
    is_sold_by_ab = fields.Boolean(string='Is Sold By AB')
    is_amazon_order = fields.Boolean('Is Amazon Order', compute='_compute_is_amazon_order')

    def is_fba(self):
        return self.fulfillment_channel == 'AFN'

    def _compute_is_amazon_order(self):
        for so in self:
            so.is_amazon_order = True

    @job(default_channel='root.amazon')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from Amazon """
        return super(AmazonSaleOrder, self).import_batch(backend, filters=filters)

    @job(default_channel='root.amazon', retry_pattern=SO_IMPORT_RETRY_PATTERN)
    @related_action(action='related_action_unwrap_binding')
    @api.model
    def import_record(self, backend, external_id, force=False):
        return super().import_record(backend, external_id, force=force)

    @api.multi
    def action_confirm(self):
        res = self.odoo_id.action_confirm()
        if res and hasattr(res, '__getitem__'):  # Button returned an action: we need to set active_id to the amazon sale order
            res.update({
                'context': {
                    'active_id': self.ids[0],
                    'active_ids': self.ids
                }
            })
        return res

    @api.multi
    def action_cancel(self):
        return self.odoo_id.action_cancel()

    @api.multi
    def action_draft(self):
        return self.odoo_id.action_draft()

    @api.multi
    def action_view_delivery(self):
        res = self.odoo_id.action_view_delivery()
        res.update({
            'context': {
                'active_id': self.ids[0],
                'active_ids': self.ids
            }
        })
        return res

    # @job(default_channel='root.amazon')
    # @api.model
    # def acknowledge_order(self, backend, external_id):
    #     with backend.work_on(self._name) as work:
    #         adapter = work.component(usage='backend.adapter')
    #         return adapter.acknowledge_order(external_id)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amazon_bind_ids = fields.One2many(
        comodel_name='amazon.sale.order',
        inverse_name='odoo_id',
        string='Amazon Bindings',
    )
    amazon_bind_id = fields.Many2one('amazon.sale.order', 'Amazon Binding', compute='_compute_amazon_bind_id')
    is_amazon_order = fields.Boolean('Is Amazon Order', compute='_compute_is_amazon_order')
    total_amount = fields.Float(
        string='Total amount',
        digits=dp.get_precision('Account'),
        related='amazon_bind_id.total_amount'
    )
    fulfillment_channel = fields.Selection(related='amazon_bind_id.fulfillment_channel')
    ship_service_level = fields.Char(string='Shipping Service Level', related='amazon_bind_id.ship_service_level')
    ship_service_level_category = fields.Char(string='Shipping Service Level Category', related='amazon_bind_id.ship_service_level_category')
    marketplace = fields.Char(string='Marketplace', related='amazon_bind_id.marketplace')
    order_type = fields.Char(string='Order Type', related='amazon_bind_id.order_type')
    is_business_order = fields.Boolean(string='Is Business Order', related='amazon_bind_id.is_business_order')
    is_prime = fields.Boolean(string='Is Prime', related='amazon_bind_id.is_prime')
    is_global_express_enabled = fields.Boolean(string='Is Global Express', related='amazon_bind_id.is_global_express_enabled')
    is_premium = fields.Boolean(string='Is Premium', related='amazon_bind_id.is_premium')
    is_sold_by_ab = fields.Boolean(string='Is Sold By AB', related='amazon_bind_id.is_sold_by_ab')

    @api.depends('amazon_bind_ids')
    def _compute_amazon_bind_id(self):
        for so in self:
            so.amazon_bind_id = so.amazon_bind_ids[:1].id

    def _compute_is_amazon_order(self):
        for so in self:
            so.is_amazon_order = False

    # @api.multi
    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     self.amazon_bind_ids.action_confirm()
    #     return res


class AmazonSaleOrderLine(models.Model):
    _name = 'amazon.sale.order.line'
    _inherit = 'amazon.binding'
    _description = 'Amazon Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    amazon_order_id = fields.Many2one(comodel_name='amazon.sale.order',
                                       string='Amazon Sale Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    odoo_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')
    backend_id = fields.Many2one(
        related='amazon_order_id.backend_id',
        string='Amazon Backend',
        readonly=True,
        store=True,
        # override 'Amazon.binding', can't be INSERTed if True:
        required=False,
    )

    @api.model
    def create(self, vals):
        amazon_order_id = vals['amazon_order_id']
        binding = self.env['amazon.sale.order'].browse(amazon_order_id)
        vals['order_id'] = binding.odoo_id.id
        binding = super(AmazonSaleOrderLine, self).create(vals)
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    amazon_bind_ids = fields.One2many(
        comodel_name='amazon.sale.order.line',
        inverse_name='odoo_id',
        string="Amazon Bindings",
    )


class SaleOrderAdapter(Component):
    _name = 'amazon.sale.order.adapter'
    _inherit = 'amazon.adapter'
    _apply_on = 'amazon.sale.order'

    def _api(self):
        return self.api_instance.orders()

    def search(self, filters):
        try:
            res = self._api().get_orders(**filters)
            if res.errors:
                _logger.error('Error in Order search: ' + str(res.errors))
        except self.api_instance.SellingApiException as e:
            raise ValidationError('SellingApiException: ' + str(e.message))
        return res.payload

    # Note that order_items_buyer_info has always returned only the order items numbers.
    def read(self, order_id,
             include_order_items=False,
             include_order_address=False,
             include_order_buyer_info=False,
             include_order_items_buyer_info=False,
             ):
        try:
            api = self._api()
            order_res = api.get_order(order_id)
            if order_res.errors:
                _logger.error('Error in Order read: ' + str(order_res.errors))
            res = order_res.payload

            if include_order_items:
                order_items_res = api.get_order_items(order_id)
                if order_items_res.errors:
                    _logger.error('Error in Order Items read: ' + str(order_items_res.errors))
                # Note that this isn't the same as the ones below to simplify later code
                # by being able to get an iterable at the top level for mapping purposes
                res['OrderItems'] = order_items_res.payload.get('OrderItems', [])

            if include_order_address:
                order_address_res = api.get_order_address(order_id)
                if order_address_res.errors:
                    _logger.error('Error in Order Address read: ' + str(order_address_res.errors))
                res['OrderAddress'] = order_address_res.payload

            if include_order_buyer_info:
                order_buyer_info_res = api.get_order_buyer_info(order_id)
                if order_buyer_info_res.errors:
                    _logger.error('Error in Order Buyer Info read: ' + str(order_buyer_info_res.errors))
                res['OrderBuyerInfo'] = order_buyer_info_res.payload

            if include_order_items_buyer_info:
                order_items_buyer_info_res = api.get_order_items_buyer_info(order_id)
                if order_items_buyer_info_res.errors:
                    _logger.error('Error in Order Items Buyer Info read: ' + str(order_items_buyer_info_res.errors))
                res['OrderItemsBuyerInfo'] = order_items_buyer_info_res.payload
        except self.api_instance.SellingApiException as e:
            if e.message.find('You exceeded your quota for the requested resource.') >= 0:
                self._sleep_rety()
            raise ValidationError('SellingApiException: ' + str(e.message))
        except RequestRateError as e:
            self._sleep_rety()
        return res

    def _sleep_rety(self):
        # we CANNOT control when the next job of this type will be scheduled (by def, the queue may even be running
        # the same jobs at the same time)
        # we CAN control how long we wait before we free up the current queue worker though...
        # Note that we can make it so that this job doesn't re-queue right away via RetryableJobError mechanisms,
        # but that is no better than the more general case of us just sleeping this long now.
        _logger.warn(' !!!!!!!!!!!!! _sleep_rety !!!!!!!!!!!!')
        sleep(SO_REQUEST_SLEEP_SECONDS)
        raise RetryableJobError('We are being throttled and will retry later.')
