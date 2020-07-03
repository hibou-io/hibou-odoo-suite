# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class RMAProductCoresMakeLines(models.TransientModel):
    _name = 'rma.product_cores.make.lines'
    _description = 'Add Product Core Lines'

    rma_id = fields.Many2one('rma.rma', string='RMA')
    line_ids = fields.One2many('rma.product_cores.make.lines.line', 'rma_make_lines_id', string='Lines')

    @api.model
    def create(self, vals):
        maker = super(RMAProductCoresMakeLines, self).create(vals)
        maker._create_lines()
        return maker

    def _create_lines(self):
        make_lines_obj = self.env['rma.product_cores.make.lines.line']
        self.rma_id._product_cores_create_make_lines(self, make_lines_obj)

    def add_lines(self):
        rma_line_obj = self.env['rma.line']
        for o in self:
            lines = o.line_ids.filtered(lambda l: l.product_uom_qty > 0.0)
            for l in lines:
                if l.qty_delivered < l.product_uom_qty:
                    raise UserError('You cannot return more than the eligible qty of this product.')
                rma_line_obj.create({
                    'rma_id': o.rma_id.id,
                    'product_id': l.product_id.id,
                    'product_uom_id': l.product_uom_id.id,
                    'product_uom_qty': l.product_uom_qty,
                })


class RMAProductCoresMakeLinesLine(models.TransientModel):
    _name = 'rma.product_cores.make.lines.line'
    _inherit = 'rma.sale.make.lines.line'

    rma_make_lines_id = fields.Many2one('rma.product_cores.make.lines')
