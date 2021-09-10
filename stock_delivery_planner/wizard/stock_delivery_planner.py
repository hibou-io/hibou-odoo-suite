from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)


class StockDeliveryPlanner(models.TransientModel):
    _name = 'stock.delivery.planner'
    _description = 'Stock Delivery Planner Wizard'

    picking_id = fields.Many2one('stock.picking', 'Transfer')
    plan_option_ids = fields.One2many('stock.delivery.planner.option', 'plan_id', 'Options')

    def create(self, values):
        planner = super(StockDeliveryPlanner, self).create(values)

        base_carriers = self.env['delivery.carrier']
        carrier_domain = self.env['ir.config_parameter'].sudo().get_param('stock.delivery.planner.carrier_domain')
        if carrier_domain:
            base_carriers = base_carriers.search(tools.safe_eval(carrier_domain))

        for carrier in base_carriers:
            rates = carrier.rate_shipment_multi(picking=planner.picking_id)
            for rate in filter(lambda r: not r.get('success'), rates):
                _logger.warning(rate.get('error_message'))
            for rate in filter(lambda r: r.get('success'), rates):
                rate = self.calculate_delivery_window(rate)
                planner.plan_option_ids |= planner.plan_option_ids.create({
                    'plan_id': self.id,
                    'carrier_id': rate['carrier'].id,
                    'price': rate['price'],
                    'date_planned': rate['date_planned'],
                    'requested_date': rate['date_delivered'],
                    'transit_days': rate['transit_days'],
                })
        return planner

    @api.model
    def calculate_delivery_window(self, rate):
        carrier = rate['carrier']
        date_planned = rate['date_planned']
        if rate.get('date_delivered'):
            date_delivered = rate['date_delivered']
            transit_days = carrier.calculate_transit_days(date_planned, date_delivered)
            if not rate.get('transit_days') or transit_days < rate.get('transit_days'):
                rate['transit_days'] = transit_days
        elif rate.get('transit_days'):
            rate['date_delivered'] = carrier.calculate_date_delivered(date_planned, rate.get('transit_days'))
        return rate


class StockDeliveryOption(models.TransientModel):
    _name = 'stock.delivery.planner.option'
    _description = 'Stock Delivery Planner Option'

    plan_id = fields.Many2one('stock.delivery.planner', 'Plan', ondelete='cascade')
    carrier_id = fields.Many2one('delivery.carrier', 'Delivery Method')
    price = fields.Float('Shipping Price')
    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Expected Delivery Date')
    transit_days = fields.Integer('Transit Days')
    sale_requested_date = fields.Datetime('Sale Order Delivery Date', related='plan_id.picking_id.sale_id.requested_date')
    days_different = fields.Float('Days Different', compute='_compute_days_different')  # use carrier calendar

    def select_plan(self):
        for option in self.filtered('carrier_id'):
            option.plan_id.picking_id.carrier_id = option.carrier_id
            return

    @api.depends('requested_date', 'sale_requested_date', 'carrier_id')
    def _compute_days_different(self):
        for option in self:
            if not option.requested_date or not option.sale_requested_date or option.requested_date.date() == option.sale_requested_date.date():
                option.days_different = 0
            elif option.requested_date < option.sale_requested_date:
                option.days_different = -1 * option.carrier_id.calculate_transit_days(option.requested_date, option.sale_requested_date)
            else:
                option.days_different = option.carrier_id.calculate_transit_days(option.sale_requested_date, option.requested_date)
