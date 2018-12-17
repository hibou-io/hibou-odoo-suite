from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.model
    def create(self, values):
        quant_model = self.sudo().env['stock.quant']
        res = super(PosOrderLine, self).create(values)
        if res.pack_lot_ids:
            lot_names = res.pack_lot_ids.mapped('lot_name')
            product_id = res.product_id.id
            quants = quant_model.search([
                ('product_id', '=', product_id),
                ('location_id', '=', res.order_id.location_id.id),
                ('lot_id', '!=', False),
                ('lot_id.name', 'in', lot_names),
            ])
            for l in res.pack_lot_ids:
                named_quants = quants.filtered(lambda q: q.lot_id.name == l.lot_name)
                for q in named_quants:
                    l.lot_id = q.lot_id
        return res

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id', 'pack_lot_ids.lot_id')
    def _compute_amount_line_all(self):
        # This is a hard override due to the closed nature of this method.
        for line in self:
            fpos = line.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id,
                                                         line.order_id.partner_id) if fpos else line.tax_ids
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            lot_ratio_sum = 0.0
            for l in line.pack_lot_ids:
                if l.lot_id:
                    lot_ratio_sum += l.lot_catch_weight_ratio
                else:
                    lot_ratio_sum += 1.0
            if lot_ratio_sum != 0.0:
                lot_ratio = lot_ratio_sum / line.qty
                price = (line.price_unit * lot_ratio) * (1 - (line.discount or 0.0) / 100.0)

            taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty,
                                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_subtotal_incl': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


class PosOrderLineLot(models.Model):
    _inherit = 'pos.pack.operation.lot'

    lot_id = fields.Many2one('stock.production.lot', string='Lot')
    lot_catch_weight_ratio = fields.Float(related='lot_id.catch_weight_ratio')
