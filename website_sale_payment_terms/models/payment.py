from odoo import models, _
import logging
_logger = logging.getLogger(__name__)


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
            order.amount_due_today,
            order.pricelist_id.currency_id.id,
            values=values,
        )

    # Override to confirm payments totaling the amount_due_today
    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        for order in self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent')):
            amount = order.amount_due_today
            if order.currency_id.compare_amounts(self.amount, amount) == 0:
                order.with_context(send_email=True).action_confirm()
            else:
                _logger.warning(
                    '<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
                    self.acquirer_id.provider, order.name, order.id,
                    amount, self.amount,
                )
                order.message_post(
                    subject=_("Amount Mismatch (%s)") % self.acquirer_id.provider,
                    body=_(
                        "The order was not confirmed despite response from the acquirer (%s): order total is %r but acquirer replied with %r.") % (
                             self.acquirer_id.provider,
                             amount,
                             self.amount,
                         )
                )
