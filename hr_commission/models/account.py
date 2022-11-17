# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_ids = fields.One2many(comodel_name='hr.commission', inverse_name='source_move_id', string='Commissions')
    commission_count = fields.Integer(string='Number of Commissions', compute='_compute_commission_count')

    @api.depends('state', 'commission_ids')
    def _compute_commission_count(self):
        for move in self:
            move.commission_count = len(move.commission_ids)
        return True

    def open_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice Commissions',
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'context': {'search_default_source_move_id': self[0].id}
        }

    def action_post(self):
        res = super(AccountMove, self).action_post()
        invoices = self.filtered(lambda m: m.is_invoice())
        if invoices:
            self.env['hr.commission'].invoice_validated(invoices)
        return res

    def action_invoice_paid(self):
        res = super(AccountMove, self).action_invoice_paid()
        self.env['hr.commission'].invoice_paid(self)
        return res

    def amount_for_commission(self, commission=None):
        # Override to exclude ineligible products
        amount = 0.0
        invoice_lines = self.invoice_line_ids.filtered(lambda l: not l.product_id.is_commission_exempt)
        sign = -1 if self.move_type in ['in_refund', 'out_refund'] else 1
        if hasattr(self, 'margin') and self.company_id.commission_amount_type == 'on_invoice_margin':
            margin_threshold = float(self.env['ir.config_parameter'].sudo().get_param('commission.margin.threshold', 0.0))
            if margin_threshold:
                invoice_lines = invoice_lines.filtered(lambda l: l.get_margin_percent() > margin_threshold)
            amount = sum(invoice_lines.mapped('margin'))
        elif self.company_id.commission_amount_type == 'on_invoice_untaxed':
            amount = sum(invoice_lines.mapped('price_subtotal'))
        else:
            amount = sum(invoice_lines.mapped('price_total'))
        return amount * sign

    def action_cancel(self):
        res = super(AccountMove, self).action_cancel()
        for move in self:
            move.sudo().commission_ids.unlink()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_margin_percent(self):
        if not self.price_subtotal:
            return 0.0
        return ((self.margin or 0.0) / self.price_subtotal) * 100.0
