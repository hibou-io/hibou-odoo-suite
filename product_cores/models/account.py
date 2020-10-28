# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import timedelta
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def post(self):
        if self._context.get('move_reverse_cancel'):
            return super(AccountMove, self).post()
        self._product_core_set_date_maturity()
        return super(AccountMove, self).post()

    def _product_core_set_date_maturity(self):
        for move in self:
            for line in move.invoice_line_ids.filtered(lambda l: l.product_id.core_ok and l.product_id.type == 'service'):
                regular_date_maturity = line.date + timedelta(days=(line.product_id.product_core_validity or 0))
                if move.type in ('in_invoice', 'in_refund', 'in_receipt'):
                    # derive from purchase
                    if move.type == 'in_refund' and line.purchase_line_id:
                        # try to date from original
                        po_move_lines = self.search([('purchase_line_id', '=', line.purchase_line_id.id)])
                        po_move_lines = po_move_lines.filtered(lambda l: l.move_id.type == 'in_invoice')
                        if po_move_lines:
                            line.date_maturity = po_move_lines[0].date_maturity or regular_date_maturity
                        else:
                            line.date_maturity = regular_date_maturity
                    else:
                        line.date_maturity = regular_date_maturity
                elif move.type in ('out_invoice', 'out_refund', 'out_receipt'):
                    # derive from sale
                    if move.type == 'out_refund' and line.sale_line_ids:
                        other_move_lines = line.sale_line_ids.mapped('invoice_lines').filtered(lambda l: l.move_id.type == 'out_invoice')
                        if other_move_lines:
                            line.date_maturity = other_move_lines[0].date_maturity or regular_date_maturity
                        else:
                            line.date_maturity = regular_date_maturity
                    else:
                        line.date_maturity = regular_date_maturity
