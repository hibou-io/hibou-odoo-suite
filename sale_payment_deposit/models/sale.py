from odoo import api, fields, models
from json import loads as json_loads


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_total_deposit = fields.Monetary(string='Deposit', compute='_amount_total_deposit')

    @api.depends('amount_total', 'payment_term_id.deposit_percentage')
    def _amount_total_deposit(self):
        for order in self:
            percent_deposit = order.amount_total * float(order.payment_term_id.deposit_percentage) / 100.0
            flat_deposite = float(order.payment_term_id.deposit_flat)
            order.amount_total_deposit = percent_deposit + flat_deposite

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._auto_deposit_invoice()
        return res

    def _auto_deposit_invoice(self):
        wizard_model = self.env['sale.advance.payment.inv'].sudo()
        for sale in self.sudo().filtered(lambda o: not o.invoice_ids and o.amount_total_deposit):
            # Create Deposit Invoices
            wizard = wizard_model.create({
                'advance_payment_method': 'fixed',
                'fixed_amount': sale.amount_total_deposit,
            })
            wizard.with_context(active_ids=sale.ids).create_invoices()
            # Validate Invoices
            sale.invoice_ids.filtered(lambda i: i.state == 'draft').post()
            # Attempt to reconcile
            sale._auto_deposit_payment_match()

    def _auto_deposit_payment_match(self):
        # Attempt to find payments that could be used on this new invoice and reconcile them.
        # Note that this probably doesn't work for a payment made on the front, see .account.PaymentTransaction
        aml_model = self.env['account.move.line'].sudo()
        for sale in self.sudo():
            for invoice in sale.invoice_ids.filtered(lambda i: i.state == 'posted'):
                outstanding = json_loads(invoice.invoice_outstanding_credits_debits_widget)
                if isinstance(outstanding, dict) and outstanding.get('content'):
                    for line in outstanding.get('content'):
                        if abs(line.get('amount', 0.0) - invoice.amount_residual) < 0.01 and line.get('id'):
                            aml = aml_model.browse(line.get('id'))
                            aml += invoice.line_ids.filtered(lambda l: l.account_id == aml.account_id)
                            if aml.reconcile():
                                break
