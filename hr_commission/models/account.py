# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    commission_ids = fields.One2many(comodel_name='hr.commission', inverse_name='invoice_id', string='Commissions')
    commission_count = fields.Integer(string='Number of Commissions', compute='_compute_commission_count')

    @api.depends('state', 'commission_ids')
    @api.multi
    def _compute_commission_count(self):
        for move in self:
            move.commission_count = len(move.commission_ids)
        return True

    @api.multi
    def open_commissions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice Commissions',
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'context': {'search_default_invoice_id': self[0].id}
        }

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        self.env['hr.commission'].invoice_validated(self)
        return res

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        self.env['hr.commission'].invoice_paid(self)
        return res

    def amount_for_commission(self):
        if hasattr(self, 'margin') and self.company_id.commission_amount_type == 'on_invoice_margin':
            sign = -1 if self.type in ['in_refund', 'out_refund'] else 1
            return self.margin * sign
        elif self.company_id.commission_amount_type == 'on_invoice_untaxed':
            return self.amount_untaxed_invoice_signed
        return self.amount_total_company_signed

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for move in self:
            move.sudo().commission_ids.unlink()
        return res
