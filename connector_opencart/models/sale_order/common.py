# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import odoo.addons.decimal_precision as dp

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError


class OpencartSaleOrder(models.Model):
    _name = 'opencart.sale.order'
    _inherit = 'opencart.binding'
    _description = 'Opencart Sale Order'
    _inherits = {'sale.order': 'odoo_id'}

    odoo_id = fields.Many2one(comodel_name='sale.order',
                              string='Sale Order',
                              required=True,
                              ondelete='cascade')
    opencart_order_line_ids = fields.One2many(
        comodel_name='opencart.sale.order.line',
        inverse_name='opencart_order_id',
        string='Walmart Order Lines'
    )

    total_amount = fields.Float(
        string='Total amount',
        digits=dp.get_precision('Account')
    )

    @job(default_channel='root.opencart')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of Sales Orders from Opencart """
        return super(OpencartSaleOrder, self).import_batch(backend, filters=filters)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    opencart_bind_ids = fields.One2many(
        comodel_name='opencart.sale.order',
        inverse_name='odoo_id',
        string="Opencart Bindings",
    )


class OpencartSaleOrderLine(models.Model):
    _name = 'opencart.sale.order.line'
    _inherit = 'opencart.binding'
    _description = 'Opencart Sale Order Line'
    _inherits = {'sale.order.line': 'odoo_id'}

    opencart_order_id = fields.Many2one(comodel_name='opencart.sale.order',
                                        string='Opencart Sale Order',
                                        required=True,
                                        ondelete='cascade',
                                        index=True)
    odoo_id = fields.Many2one(comodel_name='sale.order.line',
                              string='Sale Order Line',
                              required=True,
                              ondelete='cascade')
    backend_id = fields.Many2one(related='opencart_order_id.backend_id',
                                 string='Opencart Backend',
                                 readonly=True,
                                 store=True,
                                 required=False)

    @api.model
    def create(self, vals):
        opencart_order_id = vals['opencart_order_id']
        binding = self.env['opencart.sale.order'].browse(opencart_order_id)
        vals['order_id'] = binding.odoo_id.id
        binding = super(OpencartSaleOrderLine, self).create(vals)
        return binding


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    opencart_bind_ids = fields.One2many(
        comodel_name='opencart.sale.order.line',
        inverse_name='odoo_id',
        string="Opencart Bindings",
    )


class SaleOrderAdapter(Component):
    _name = 'opencart.sale.order.adapter'
    _inherit = 'opencart.adapter'
    _apply_on = 'opencart.sale.order'

    def search(self, filters=None):
        api_instance = self.api_instance
        orders_response = api_instance.orders.all(id_larger_than=filters.get('after_id'))
        if 'error' in orders_response and orders_response['error']:
            raise ValidationError(str(orders_response))

        if 'data' not in orders_response or not isinstance(orders_response['data'], list):
            return []

        orders = orders_response['data']
        return map(lambda o: o['order_id'], orders)

    def read(self, id):
        api_instance = self.api_instance
        record = api_instance.orders.get(id)
        if 'data' in record and record['data']:
            return record['data']
        raise RetryableJobError('Order "' + str(id) + '" did not return an order response. ' + str(record))
