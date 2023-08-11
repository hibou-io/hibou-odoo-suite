from odoo import models, _
from odoo.tools import format_amount
import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # Override to confirm payments totaling the amount_due_today
    def _check_amount_and_confirm_order(self):
        confirmed_orders = self.env['sale.order']
        for tx in self:
            # We only support the flow where exactly one quotation is linked to a transaction and
            # vice versa.
            if len(tx.sale_order_ids) == 1:
                quotation = tx.sale_order_ids.filtered(lambda so: so.state in ('draft', 'sent') and so.amount_due_today)
                if quotation and len(quotation.transaction_ids.filtered(
                    lambda tx: tx.state in ('authorized', 'done')  # Only consider confirmed tx
                )) == 1:
                    # Check if the SO is fully paid (amount_due_today)
                    if quotation.currency_id.compare_amounts(tx.amount, quotation.amount_due_today) == 0:
                        quotation.with_context(send_email=True).action_confirm()
                        confirmed_orders |= quotation
                    else:
                        _logger.warning(
                            '<%(provider)s> transaction TERMS AMOUNT MISMATCH for order %(so_name)s '
                            '(ID %(so_id)s): expected %(so_amount)s, got %(tx_amount)s', {
                                'provider': tx.provider_code,
                                'so_name': quotation.name,
                                'so_id': quotation.id,
                                'so_amount': format_amount(
                                    quotation.env, quotation.amount_due_today, quotation.currency_id
                                ),
                                'tx_amount': format_amount(tx.env, tx.amount, tx.currency_id),
                            },
                        )
        return confirmed_orders | super()._check_amount_and_confirm_order()
