# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _values_for_payment_invoice_line(self, line, currency_id):
        sign = 1.0 if self.payment_type == 'outbound' else -1.0
        i_write_off_amount = -line.difference if line.difference and line.close_balance else 0.0
        i_amount_currency = (line.amount + i_write_off_amount) if currency_id else 0.0
        i_amount = sign * (line.amount + i_write_off_amount)
        return {
            'amount_currency': i_amount_currency,
            'currency_id': currency_id,
            'debit': i_amount if i_amount > 0.0 else 0.0,
            'credit': -i_amount if i_amount < 0.0 else 0.0,
        }
