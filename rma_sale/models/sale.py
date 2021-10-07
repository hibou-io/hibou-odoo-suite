# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rma_count = fields.Integer(string='RMA Count', compute='_compute_rma_count', compute_sudo=True)
    rma_ids = fields.One2many('rma.rma', 'sale_order_id', string='RMAs')

    @api.depends('rma_ids')
    def _compute_rma_count(self):
        for so in self:
            so.rma_count = len(so.rma_ids)
