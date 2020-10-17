# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def copy(self, default=None):
        new_po = super(PurchaseOrder, self).copy(default=default)
        for line in new_po.order_line.filtered(lambda l: l.product_id.core_ok and not l.core_line_id):
            line.unlink()
        return new_po


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    core_line_id = fields.Many2one('purchase.order.line', string='Core Purchase Line', copy=False)

    @api.model
    def create(self, values):
        res = super(PurchaseOrderLine, self).create(values)
        other_product = res.product_id.get_purchase_core_service(res.order_id.partner_id)
        if other_product:
            values['product_id'] = other_product.id
            values['name'] = other_product.name
            values['price_unit'] = other_product.list_price
            values['core_line_id'] = res.id
            other_line = self.create(values)
            other_line._compute_tax_id()
        return res

    def write(self, values):
        res = super(PurchaseOrderLine, self).write(values)
        if 'product_id' in values or 'product_qty' in values or 'product_uom' in values:
            self.filtered(lambda l: not l.core_line_id)\
                .mapped('order_id.order_line')\
                .filtered('core_line_id')\
                ._update_core_line()
        return res

    def unlink(self):
        for line in self:
            if line.core_line_id and line.core_line_id and not self.env.user.has_group('purchase.group_purchase_user'):
                raise UserError(_('You cannot delete a core line while the original still exists.'))
            # Unlink any linked core lines.
            other_line = line.order_id.order_line.filtered(lambda l: l.core_line_id == line)
            if other_line and other_line not in self:
                other_line.write({'core_line_id': False})
                other_line.unlink()
        return super(PurchaseOrderLine, self).unlink()

    def _update_core_line(self):
        for line in self:
            if line.core_line_id and line.core_line_id.product_id.get_purchase_core_service(line.order_id.partner_id):
                line.update({
                    'product_id': line.core_line_id.product_id.get_purchase_core_service(line.order_id.partner_id).id,
                    'product_qty': line.core_line_id.product_qty,
                    'product_uom': line.core_line_id.product_uom.id,
                })
            elif line.core_line_id:
                line.unlink()
