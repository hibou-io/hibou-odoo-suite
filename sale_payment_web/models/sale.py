from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_payment_register(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_form_multi').id,
            'context': {'active_ids': self.ids, 'active_model': 'sale.order'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
