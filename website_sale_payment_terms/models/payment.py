from odoo import models, _


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def render_sale_button(self, order, submit_txt=None, render_values=None):
        values = {
            'partner_id': order.partner_id.id,
            'type': self.type,
        }
        if render_values:
            values.update(render_values)
        # Not very elegant to do that here but no choice regarding the design.
        self._log_payment_transaction_sent()
        return self.acquirer_id.with_context(submit_class='btn btn-primary', submit_txt=submit_txt or _('Pay Now')).sudo().render(
            self.reference,
            order.amount_total_deposit or order.amount_total,
            order.pricelist_id.currency_id.id,
            values=values,
        )
