from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manual_payment_ids = fields.One2many('account.payment', 'sale_order_id', string='Manual Payments')
    manual_amount_registered_payment = fields.Monetary('Manually Registered Amount', compute='_compute_manual_amount_registered_payment')
    manual_amount_remaining = fields.Monetary('Remaining Amount Due', compute='_compute_manual_amount_registered_payment')

    @api.depends('manual_payment_ids.amount', 'amount_total')
    def _compute_manual_amount_registered_payment(self):
        for so in self:
            so.manual_amount_registered_payment = sum(so.manual_payment_ids.mapped('amount'))
            so.manual_amount_remaining = so.amount_total - so.manual_amount_registered_payment


    def action_manual_payments(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        domain = action['domain'] or '[]'
        domain = safe_eval(domain)
        domain.append(('id', 'in', self.manual_payment_ids.ids))
        action['domain'] = domain
        return action

    def action_payment_register(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {'active_ids': self.ids, 'active_model': 'sale.order'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
