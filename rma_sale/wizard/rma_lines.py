# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class RMASaleMakeLines(models.TransientModel):
    _name = 'rma.sale.make.lines'
    _description = 'Add SO Lines'

    rma_id = fields.Many2one('rma.rma', string='RMA')
    line_ids = fields.One2many('rma.sale.make.lines.line', 'rma_make_lines_id', string='Lines')


    @api.model
    def create(self, vals):
        maker = super(RMASaleMakeLines, self).create(vals)
        maker._create_lines()
        return maker

    def _line_values(self, so_line):
        return {
            'rma_make_lines_id': self.id,
            'product_id': so_line.product_id.id,
            'qty_ordered': so_line.product_uom_qty,
            'qty_delivered': so_line.qty_delivered,
            'qty_invoiced': so_line.qty_invoiced,
            'product_uom_qty': 0.0,
            'product_uom_id': so_line.product_uom.id,
            'validity': self.rma_id.template_id._rma_sale_line_validity(so_line),
        }

    def _create_lines(self):
        make_lines_obj = self.env['rma.sale.make.lines.line']

        if self.rma_id.template_usage == 'sale_order' and self.rma_id.sale_order_id:
            for l in self.rma_id.sale_order_id.order_line:
                self.line_ids |= make_lines_obj.create(self._line_values(l))

    def add_lines(self):
        rma_line_obj = self.env['rma.line']
        for o in self:
            lines = o.line_ids.filtered(lambda l: l.product_uom_qty > 0.0)
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                if lines.filtered(lambda l: not l.validity):
                    raise UserError('One or more items are not eligible for return.')
                if lines.filtered(lambda l: l.validity == 'expired'):
                    raise UserError('One or more items are past their return period.')
            for l in lines:
                rma_line_obj.create({
                    'rma_id': o.rma_id.id,
                    'product_id': l.product_id.id,
                    'product_uom_id': l.product_uom_id.id,
                    'product_uom_qty': l.product_uom_qty,
                })


class RMASOMakeLinesLine(models.TransientModel):
    _name = 'rma.sale.make.lines.line'
    _description = 'RMA Sale Make Lines Line'

    rma_make_lines_id = fields.Many2one('rma.sale.make.lines')
    product_id = fields.Many2one('product.product', string="Product")
    qty_ordered = fields.Float(string='Ordered')
    qty_invoiced = fields.Float(string='Invoiced')
    qty_delivered = fields.Float(string='Delivered')
    product_uom_qty = fields.Float(string='QTY')
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
    validity = fields.Selection([
        ('', 'Not Eligible'),
        ('valid', 'Eligible'),
        ('expired', 'Expired'),
    ], string='Validity')
