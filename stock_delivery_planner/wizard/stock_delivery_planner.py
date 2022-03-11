# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class StockDeliveryPlanner(models.TransientModel):
    _name = 'stock.delivery.planner'
    _description = 'Stock Delivery Planner Wizard'

    picking_id = fields.Many2one('stock.picking', 'Transfer')
    plan_option_ids = fields.One2many('stock.delivery.planner.option', 'plan_id', 'Options')
    packages_planned = fields.Boolean(compute='_compute_packages_planned')

    @api.depends('plan_option_ids.selection')
    def _compute_packages_planned(self):
        for wiz in self:
            packages = wiz.picking_id.package_ids
            if not packages:
                wiz.packages_planned = False
            selected_options = wiz.plan_option_ids.filtered(lambda p: p.selection == 'selected')
            wiz.packages_planned = len(selected_options) == len(packages)

    def _get_carriers(self):
        self.ensure_one()
        base_carriers = self.picking_id.picking_type_id.warehouse_id.delivery_planner_carrier_ids
        if not base_carriers:
            carrier_ids = self.env['ir.config_parameter'].sudo().get_param('stock.delivery.planner.carrier_ids.%s' % (self.env.user.company_id.id, ))
            if carrier_ids:
                try:
                    carrier_ids = [int(c) for c in carrier_ids.split(',')]
                    base_carriers = base_carriers.browse(carrier_ids)
                except:
                    pass
        return base_carriers.sudo()

    def create(self, values):
        planner = super(StockDeliveryPlanner, self).create(values)
        base_carriers = planner._get_carriers()

        for carrier in base_carriers:
            try:
                rates = carrier.rate_shipment_multi(picking=planner.picking_id)
                for rate in filter(lambda r: not r.get('success'), rates):
                    _logger.warning(rate.get('error_message'))
                for rate in filter(lambda r: r.get('success'), rates):
                    rate = self.calculate_delivery_window(rate)
                    # added late in API dev cycle
                    package = rate.get('package') or self.env['stock.quant.package'].browse()
                    planner.plan_option_ids |= planner.plan_option_ids.create({
                        'plan_id': self.id,
                        'carrier_id': rate['carrier'].id,
                        'package_id': package.id,
                        'price': rate['price'],
                        'date_planned': rate['date_planned'],
                        'requested_date': rate.get('date_delivered', False),
                        'transit_days': rate.get('transit_days', 0),
                    })
            except (UserError, ValidationError) as e:
                _logger.warning('Exception during delivery planning. %s' % str(e))
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

    def action_plan(self):
        self.ensure_one()
        selected_package_options = self.plan_option_ids.filtered(lambda o: o.package_id and o.selection == 'selected')
        selected_package_options._plan()
        return {"type": "ir.actions.act_window_close"}


class StockDeliveryOption(models.TransientModel):
    _name = 'stock.delivery.planner.option'
    _description = 'Stock Delivery Planner Option'

    plan_id = fields.Many2one('stock.delivery.planner', 'Plan', ondelete='cascade')
    carrier_id = fields.Many2one('delivery.carrier', 'Delivery Method')
    package_id = fields.Many2one('stock.quant.package', 'Package')
    price = fields.Float('Shipping Price')
    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Expected Delivery Date')
    transit_days = fields.Integer('Transit Days')
    sale_requested_date = fields.Datetime('Sale Order Delivery Date', related='plan_id.picking_id.sale_id.requested_date')
    days_different = fields.Float('Days Different', compute='_compute_days_different')  # use carrier calendar
    selection = fields.Selection([
        ('', 'None'),
        ('selected', 'Selected'),
        ('deselected', 'De-selected')
    ])

    def _plan(self):
        # this is intended to be used during selecting a whole plan
        for option in self:
            option.package_id.write({
                'carrier_id': option.carrier_id.id,
            })

    def select_plan(self):
        self.ensure_one()
        self.selection = 'selected'
        if self.package_id:
            # need to deselect other options for this package
            deselected = self.plan_id.plan_option_ids.filtered(lambda o: o.package_id == self.package_id and o != self)
            deselected.write({'selection': 'deselected'})
            return {
                'name': _('Delivery Rate Planner'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.delivery.planner',
                'res_id': self.plan_id.id,
                'target': 'new',
            }
        else:
            # Select plan for whole shipment
            self.plan_id.picking_id.carrier_id = self.carrier_id
            return {"type": "ir.actions.act_window_close"}

    @api.depends('requested_date', 'sale_requested_date', 'carrier_id')
    def _compute_days_different(self):
        for option in self:
            if not option.requested_date or not option.sale_requested_date or option.requested_date.date() == option.sale_requested_date.date():
                option.days_different = 0
            elif option.requested_date < option.sale_requested_date:
                option.days_different = -1 * option.carrier_id.calculate_transit_days(option.requested_date, option.sale_requested_date)
            else:
                option.days_different = option.carrier_id.calculate_transit_days(option.sale_requested_date, option.requested_date)
