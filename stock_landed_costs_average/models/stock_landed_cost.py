from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def get_valuation_lines(self):
        """
        Override for allowing Average value inventory.
        :return: list of new line values
        """
        lines = []

        for move in self.mapped('picking_ids').mapped('move_lines'):
            # Only allow for real time valuated products with 'average' or 'fifo' cost
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average'):
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.value,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct picking'))
        return lines

    @api.multi
    def button_validate(self):
        """
        Override to directly set new standard_price on product if average costed.
        :return: True
        """
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if any(not cost.valuation_adjustment_lines for cost in self):
            raise UserError(_('No valuation adjustments lines. You should maybe recompute the landed costs.'))
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                # Prorate the value at what's still in stock
                _logger.info('(line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost')
                _logger.info('(%s / %s) * %s' % (line.move_id.remaining_qty, line.move_id.product_qty, line.additional_landed_cost))
                cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
                _logger.info('cost_to_add: ' + str(cost_to_add))

                new_landed_cost_value = line.move_id.landed_cost_value + line.additional_landed_cost
                line.move_id.write({
                    'landed_cost_value': new_landed_cost_value,
                    'value': line.move_id.value + cost_to_add,
                    'remaining_value': line.move_id.remaining_value + cost_to_add,
                    'price_unit': (line.move_id.value + new_landed_cost_value) / line.move_id.product_qty,
                })
                # `remaining_qty` is negative if the move is out and delivered products that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - line.move_id.remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

                # Need to set the standard price directly on the product.
                if line.product_id.cost_method == 'average':
                    # From product.do_change_standard_price
                    quant_locs = self.env['stock.quant'].sudo().read_group([('product_id', '=', line.product_id.id)],
                                                                           ['location_id'], ['location_id'])
                    quant_loc_ids = [loc['location_id'][0] for loc in quant_locs]
                    locations = self.env['stock.location'].search(
                        [('usage', '=', 'internal'), ('company_id', '=', self.env.user.company_id.id),
                         ('id', 'in', quant_loc_ids)])
                    qty_available = line.product_id.with_context(location=locations.ids).qty_available
                    total_cost = (qty_available * line.product_id.standard_price) + cost_to_add
                    line.product_id.write({'standard_price': total_cost / qty_available})

            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()
        return True