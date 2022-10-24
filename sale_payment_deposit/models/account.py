from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    deposit_percentage = fields.Float(string='Deposit Percentage',
                                      help='Require Percentage deposit when paying on the front end.')
    deposit_flat = fields.Float(string='Deposit Flat',
                                      help='Require Flat deposit when paying on the front end.')


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _post_process_after_done(self):
        now = fields.Datetime.now()
        res = super(PaymentTransaction, self)._post_process_after_done()

        # Post Process Payments made on the front of the website, reconciling to Deposit.
        for transaction in self.filtered(lambda t: t.payment_id
                                                   and t.sale_order_ids
                                                   and sum(t.sale_order_ids.mapped('amount_total_deposit'))
                                                   and not t.invoice_ids and (now - t.date).seconds < 1200):
            if not transaction.sale_order_ids.mapped('invoice_ids'):
                # don't process ones that we might still be able to process later...
                transaction.write({'is_processed': False})
            else:
                # we have a payment and could attempt to reconcile to an invoice
                # Leave the payment in 'is_processed': True
                transaction.sale_order_ids._auto_deposit_payment_match()
        return res
