# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import odoo.addons.decimal_precision as dp
from urllib.parse import parse_qs

from odoo import models, fields, api
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)


class WalmartSaleOrder(models.Model):
    _name = 'walmart.sale.order'
    _inherit = 'walmart.binding'
    _description = 'Walmart Sale Order'
    _inherits = {'sale.order': 'odoo_id'}

    odoo_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    walmart_order_line_ids = fields.One2many(
        comodel_name='walmart.sale.order.line',
        inverse_name='walmart_order_id',
        string='Walmart Order Lines'
    )
    customer_order_id = fields.Char(string='Customer Order ID')
    total_amount = fields.Float(
        string='Total amount',
        digits=dp.get_precision('Account')
    )
    total_amount_tax = fields.Float(
        string='Total amount w. tax',
        digits=dp.get_precision('Account')
    )
    shipping_method_code = fields.Selection(
        selection=[
            ('Value', 'Value'),
            ('Standard', 'Standard'),
            ('Express', 'Express'),
            ('Oneday', 'Oneday'),
            ('Freight', 'Freight'),
        ],
        string='Shipping Method Code',
        required=False,
    )

    @job(default_channel='root.walmart')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from Walmart """
        return super(WalmartSaleOrder, self).import_batch(backend, filters=filters)

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.backend_id.acknowledge_order == 'order_confirm':
                self.with_delay().acknowledge_order(order.backend_id, order.external_id)

    @job(default_channel='root.walmart')
    @api.model
    def acknowledge_order(self, backend, external_id):
        with backend.work_on(self._name) as work:
            adapter = work.component(usage='backend.adapter')
            return adapter.acknowledge_order(external_id)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    walmart_bind_ids = fields.One2many(
        comodel_name='walmart.sale.order',
        inverse_name='odoo_id',
        string="Walmart Bindings",
    )

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.walmart_bind_ids.action_confirm()
        return res


class WalmartSaleOrderLine(models.Model):
    _name = 'walmart.sale.order.line'
    _inherit = 'walmart.binding'
    _description = 'Walmart Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    walmart_order_id = fields.Many2one(comodel_name='walmart.sale.order',
                                       string='Walmart Sale Order',
                                       required=True,
                                       ondelete='cascade',
                                       index=True)
    odoo_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')
    backend_id = fields.Many2one(
        related='walmart_order_id.backend_id',
        string='Walmart Backend',
        readonly=True,
        store=True,
        # override 'walmart.binding', can't be INSERTed if True:
        required=False,
    )
    tax_rate = fields.Float(string='Tax Rate',
                            digits=dp.get_precision('Account'))
    walmart_number = fields.Char(string='Walmart lineNumber')
    # notes = fields.Char()

    @api.model
    def create(self, vals):
        walmart_order_id = vals['walmart_order_id']
        binding = self.env['walmart.sale.order'].browse(walmart_order_id)
        vals['order_id'] = binding.odoo_id.id
        binding = super(WalmartSaleOrderLine, self).create(vals)
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    walmart_bind_ids = fields.One2many(
        comodel_name='walmart.sale.order.line',
        inverse_name='odoo_id',
        string="Walmart Bindings",
    )


    @api.multi
    def _compute_tax_id(self):
        """
        This overrides core behavior because we need to get the order_line into the order
        to be able to compute Walmart taxes.
        :return:
        """
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id, order_line=line) if fpos else taxes



class SaleOrderAdapter(Component):
    _name = 'walmart.sale.order.adapter'
    _inherit = 'walmart.adapter'
    _apply_on = 'walmart.sale.order'

    def search(self, from_date=None, next_cursor=None):
        """

        :param filters: Dict of filters
        :param from_date:
        :param next_cursor:
        :return: List
        """
        if next_cursor:
            # next_cursor looks like '?somefield=xxx&blah=yyy'
            arguments = parse_qs(next_cursor.strip('?'))
        else:
            arguments = {'createdStartDate': from_date.isoformat()}

        api_instance = self.api_instance
        orders_response = api_instance.orders.all(**arguments)
        _logger.debug(orders_response)

        if not 'list' in orders_response:
            return []

        # 'meta' may not be there (though it is in the example on the API docs even when nextCursor is none)
        next = orders_response.get('list', {}).get('meta', {}).get('nextCursor')
        if next:
            self.env[self._apply_on].with_delay().import_batch(
                self.backend_record,
                filters={'next_cursor': next}
            )

        orders = orders_response['list']['elements']['order']
        return map(lambda o: o['purchaseOrderId'], orders)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        api_instance = self.api_instance
        record = api_instance.orders.get(id)
        if 'order' in record:
            order = record['order']
            order['orderLines'] = order['orderLines']['orderLine']
            return order
        raise RetryableJobError('Order "' + str(id) + '" did not return an order response.')

    def acknowledge_order(self, id):
        """ Returns the order after ack
        :rtype: dict
        """
        _logger.info('BEFORE ACK ' + str(id))
        api_instance = self.api_instance
        record = api_instance.orders.acknowledge(id)
        _logger.info('AFTER ACK RECORD: ' + str(record))
        if 'order' in record:
            return record['order']
        raise RetryableJobError('Acknowledge Order "' + str(id) + '" did not return an order response.')

