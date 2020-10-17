# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class RMAPickingMakeLines(models.TransientModel):
    _name = 'rma.picking.make.lines'
    _description = 'Add Picking Lines'

    rma_id = fields.Many2one('rma.rma', string='RMA')
    line_ids = fields.One2many('rma.picking.make.lines.line', 'rma_make_lines_id', string='Lines')


    @api.model
    def create(self, vals):
        maker = super(RMAPickingMakeLines, self).create(vals)
        maker._create_lines()
        return maker

    def _line_values(self, move):
        return {
            'rma_make_lines_id': self.id,
            'product_id': move.product_id.id,
            'qty_ordered': move.product_uom_qty,
            'qty_delivered': move.product_qty,
            'product_uom_qty': 0.0,
            'product_uom_id': move.product_uom.id,
        }

    def _create_lines(self):
        make_lines_obj = self.env['rma.picking.make.lines.line']

        if self.rma_id.template_usage == 'stock_picking' and self.rma_id.stock_picking_id:
            for l in self.rma_id.stock_picking_id.move_lines:
                self.line_ids |= make_lines_obj.create(self._line_values(l))

    def add_lines(self):
        rma_line_obj = self.env['rma.line']
        for o in self:
            lines = o.line_ids.filtered(lambda l: l.product_uom_qty > 0.0)
            for l in lines:
                rma_line_obj.create({
                    'rma_id': o.rma_id.id,
                    'product_id': l.product_id.id,
                    'product_uom_id': l.product_uom_id.id,
                    'product_uom_qty': l.product_uom_qty,
                })


class RMAPickingMakeLinesLine(models.TransientModel):
    _name = 'rma.picking.make.lines.line'
    _description = 'RMA Picking Make Lines Line'

    rma_make_lines_id = fields.Many2one('rma.picking.make.lines')
    product_id = fields.Many2one('product.product', string="Product")
    qty_ordered = fields.Float(string='Ordered')
    qty_delivered = fields.Float(string='Delivered')
    product_uom_qty = fields.Float(string='QTY')
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
