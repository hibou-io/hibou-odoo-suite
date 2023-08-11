from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_due_today = fields.Float('Due Now', compute='_compute_amount_due_today',
                                    help='Amount due at checkout on the website.')

    @api.depends('amount_total', 'payment_term_id')
    def _compute_amount_due_today(self):
        date_today = fields.Date.today()
        for order in self:
            amount = order.amount_total
            if order.website_id and order.amount_total > order.website_id.payment_deposit_threshold and order.payment_term_id:
                terms = order.payment_term_id._compute_terms(
                    date_ref=date_today,
                    currency=order.currency_id,
                    tax_amount_currency=order.amount_tax,
                    tax_amount=order.amount_tax,
                    untaxed_amount_currency=order.amount_untaxed,
                    untaxed_amount=order.amount_untaxed,
                    company=order.company_id,
                    sign=1,
                )
                term_amount = [term['foreign_amount'] for term in terms if term['date'] == date_today]
                term_amount = term_amount and term_amount[0] or 0.0
                amount = term_amount if term_amount > order.amount_total_deposit else order.amount_total_deposit
            order.amount_due_today = amount

    def _check_payment_term_quotation(self, payment_term_id):
        self.ensure_one()
        if payment_term_id and self.payment_term_id.id != payment_term_id:
            # TODO how can we set a default if we can only set ones partner has assigned...
            # Otherwise.. how do we prevent using any payment term by ID?
            payment_term = self.env['account.payment.term'].sudo().browse(payment_term_id)
            if not payment_term.exists():
                raise Exception('Could not find payment terms.')
            self.payment_term_id = payment_term
