# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def copy(self, default=None):
        new_so = super(SaleOrder, self).copy(default=default)
        for line in new_so.order_line.filtered(lambda l: l.product_id.core_ok and not l.core_line_id):
            line.unlink()
        return new_so


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    core_line_id = fields.Many2one('sale.order.line', string='Core Sale Line', copy=False)

    @api.model
    def create(self, values):
        res = super(SaleOrderLine, self).create(values)
        if res.product_id.product_core_service_id:
            other_product = res.product_id.product_core_service_id
            values['product_id'] = other_product.id
            values['name'] = other_product.name
            values['price_unit'] = other_product.list_price
            values['core_line_id'] = res.id
            other_line = self.create(values)
            other_line._compute_tax_id()
        return res

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        if 'product_id' in values or 'product_uom_qty' in values or 'product_uom' in values:
            for line in self.filtered(lambda l: not l.core_line_id):
                line.mapped('order_id.order_line').filtered(lambda l: l.core_line_id == line)._update_core_line()
        return res

    def unlink(self):
        for line in self:
            if line.core_line_id and line.core_line_id and not self.env.user.has_group('sales_team.group_sale_manager'):
                raise UserError(_('You cannot delete a core line while the original still exists.'))
            # Unlink any linked core lines.
            other_line = line.order_id.order_line.filtered(lambda l: l.core_line_id == line)
            if other_line and other_line not in self:
                other_line.write({'core_line_id': False})
                other_line.unlink()
        return super(SaleOrderLine, self).unlink()

    def _update_core_line(self):
        for line in self:
            if line.core_line_id and line.core_line_id.product_id.product_core_service_id:
                line.write({
                    'product_id': line.core_line_id.product_id.product_core_service_id.id,
                    'product_uom_qty': line.core_line_id.product_uom_qty,
                    'product_uom': line.core_line_id.product_uom.id,
                })
            elif line.core_line_id:
                line.unlink()

    @api.depends('core_line_id.qty_delivered')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self.filtered(lambda l: l.core_line_id):
            line.qty_delivered = line.core_line_id.qty_delivered
