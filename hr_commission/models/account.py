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
        if hasattr(self, 'margin') and self.company_id.commission_amount_type == 'on_invoice_margin':
            sign = -1 if self.move_type in ['in_refund', 'out_refund'] else 1
            return self.margin * sign
        elif self.company_id.commission_amount_type == 'on_invoice_untaxed':
            return self.amount_untaxed_signed
        return self.amount_total_signed

    def action_cancel(self):
        res = super(AccountMove, self).action_cancel()
        for move in self:
            move.sudo().commission_ids.unlink()
        return res
