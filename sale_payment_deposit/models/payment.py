from odoo import models, _

import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Override to confirm payments totaling the amount_total_deposit
    def _check_amount_and_confirm_order(self):
        self.ensure_one()
        for order in self.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent')):
            # default amount as originally calculated
            amount = order.amount_total
            if order.amount_total_deposit:
                amount = order.amount_total_deposit
            if order.currency_id.compare_amounts(self.amount, amount) == 0:
                order.with_context(send_email=True).action_confirm()
            else:
                _logger.warning(
                    '<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
                    self.acquirer_id.provider,order.name, order.id,
                    amount, self.amount,
                )
                order.message_post(
                    subject=_("Amount Mismatch (%s)") % self.acquirer_id.provider,
                    body=_("The order was not confirmed despite response from the acquirer (%s): order total is %r but acquirer replied with %r.") % (
                        self.acquirer_id.provider,
                        amount,
                        self.amount,
                    )
                )
