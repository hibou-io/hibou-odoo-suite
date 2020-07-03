# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def send_to_shipper(self):
        res = False
        for pick in self.filtered(lambda p: not p.carrier_tracking_ref):
            # deliver full order if no items are done.
            pick_has_no_done = sum(pick.move_line_ids.mapped('qty_done')) == 0
            if pick_has_no_done:
                pick._rma_complete()
            res = super(StockPicking, pick).send_to_shipper()
            if pick_has_no_done:
                pick._rma_complete_reverse()
        return res

    def _rma_complete(self):
        for line in self.move_line_ids:
            line.qty_done = line.product_uom_qty

    def _rma_complete_reverse(self):
        self.move_line_ids.write({'qty_done': 0.0})
