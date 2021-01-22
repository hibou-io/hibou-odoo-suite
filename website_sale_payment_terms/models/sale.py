from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_payment_term_quotation(self, payment_term_id):
        self.ensure_one()
        if payment_term_id and self.payment_term_id.id != payment_term_id:
            # TODO how can we set a default if we can only set ones partner has assigned...
            # Otherwise.. how do we prevent using any payment term by ID?
            payment_term = self.env['account.payment.term'].sudo().browse(payment_term_id)
            if not payment_term.exists():
                raise Exception('Could not find payment terms.')
            self.write({
                'payment_term_id': payment_term_id,
                'require_payment': bool(payment_term.deposit_percentage) or bool(payment_term.deposit_flat),
            })
