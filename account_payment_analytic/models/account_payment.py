from odoo import api, fields, models


class AccountAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')


class AccountRegisterPayment(models.TransientModel):
    _inherit = 'account.register.payments'

    @api.multi
    def _prepare_payment_vals(self, invoices):
        res = super(AccountRegisterPayment, self)._prepare_payment_vals(invoices)
        if self.account_analytic_id:
            res['account_analytic_id'] = self.account_analytic_id.id
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        res = super(AccountPayment, self)._get_shared_move_line_vals(debit, credit, amount_currency, move_id, invoice_id=invoice_id)
        if self.account_analytic_id:
            # Note the field name is not an accident! res is `account.move.line`
            res['analytic_account_id'] = self.account_analytic_id.id
        return res
