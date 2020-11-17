from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipping_account_id = fields.Many2one('partner.shipping.account', string='Shipping Account')
    require_insurance = fields.Selection([
            ('auto', 'Automatic'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Require Insurance', default='auto',
        help='If your carrier supports it, auto should be calculated off of the "Automatic Insurance Value" field.')

    @api.onchange('carrier_id')
    def _onchange_carrier_id_for_priority(self):
        for picking in self:
            if picking.carrier_id and picking.carrier_id.procurement_priority:
                picking.priority = picking.carrier_id.procurement_priority

    @api.model
    def create(self, values):
        origin = values.get('origin')
        if origin and not values.get('shipping_account_id'):
            so = self.env['sale.order'].search([('name', '=', str(origin))], limit=1)
            if so and so.shipping_account_id:
                values['shipping_account_id'] = so.shipping_account_id.id
        carrier_id = values.get('carrier_id')
        if carrier_id:
            carrier = self.env['delivery.carrier'].browse(carrier_id)
            if carrier.procurement_priority:
                values['priority'] = carrier.procurement_priority

        res = super(StockPicking, self).create(values)
        return res

    def declared_value(self):
        self.ensure_one()
        cost = sum([(l.product_id.standard_price * l.qty_done) for l in self.move_line_ids] or [0.0])
        if not cost:
            # Assume Full Value
            cost = sum([(l.product_id.standard_price * l.product_uom_qty) for l in self.move_lines] or [0.0])
        return cost
