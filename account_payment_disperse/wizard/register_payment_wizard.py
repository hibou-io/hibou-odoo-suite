from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    is_manual_disperse = fields.Boolean(string='Disperse Manually')
    invoice_line_ids = fields.One2many('account.register.payments.invoice.line', 'wizard_id', string='Invoices')
    writeoff_journal_id = fields.Many2one('account.journal', string='Write-off Journal')
    due_date_cutoff = fields.Date(string='Due Date Cutoff', default=fields.Date.today)

    @api.model
    def default_get(self, fields):
        rec = super(AccountRegisterPayments, self).default_get(fields)
        if 'invoice_ids' in rec:
            invoice_ids = rec['invoice_ids'][0][2]
            rec['invoice_line_ids'] = [(0, 0, {'invoice_id': i, 'amount': 0.0}) for i in invoice_ids]
        return rec

    @api.multi
    def create_payments(self):
        for payment in self.filtered(lambda p: p.is_manual_disperse):
            line_amount = sum(payment.invoice_line_ids.mapped('amount'))
            if abs(line_amount - payment.amount) >= 0.01:
                raise ValidationError('Cannot pay for %0.2f worth of invoices with %0.2f total.' %
                                      (line_amount, payment.amount))
            if not payment.writeoff_journal_id and payment.invoice_line_ids.filtered(lambda l: l.writeoff_acc_id):
                raise ValidationError('Cannot write off without a write off journal.')
        new_self = self.with_context(payment_wizard_id=self.id)
        return super(AccountRegisterPayments, new_self).create_payments()

    @api.multi
    def action_fill_residual(self):
        for payment in self:
            for line in payment.invoice_line_ids:
                line.amount = line.residual
            action = self.env.ref('account.action_account_payment_from_invoices').read()[0]
            action['res_id'] = payment.id
            return action

    @api.multi
    def action_fill_residual_due(self):
        for payment in self:
            for line in payment.invoice_line_ids:
                line.amount = line.residual_due
            action = self.env.ref('account.action_account_payment_from_invoices').read()[0]
            action['res_id'] = payment.id
            return action


class AccountRegisterPaymentsInvoiceLine(models.TransientModel):
    _name = 'account.register.payments.invoice.line'

    wizard_id = fields.Many2one('account.register.payments')
    invoice_id = fields.Many2one('account.invoice', string='Invoice', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', compute='_compute_balances', compute_sudo=True)
    residual = fields.Float(string='Remaining', compute='_compute_balances', compute_sudo=True)
    residual_due = fields.Float(string='Due', compute='_compute_balances', compute_sudo=True)
    difference = fields.Float(string='Difference', default=0.0)
    amount = fields.Float(string='Amount')
    writeoff_acc_id = fields.Many2one('account.account', string='Write-off Account')

    @api.depends('invoice_id', 'wizard_id.due_date_cutoff', 'invoice_id.partner_id')
    def _compute_balances(self):
        for line in self:
            # Bug in the ORM 12.0?  The invoice is set, but there is no residual
            # on anything other than the first invoice/line processed.
            invoice = line.invoice_id.browse(line.invoice_id.id)
            residual = invoice.residual

            cutoff_date = line.wizard_id.due_date_cutoff
            total_amount = 0.0
            total_reconciled = 0.0
            for move_line in invoice.move_id.line_ids.filtered(lambda r: (
                    not r.reconciled
                    and r.account_id.internal_type in ('payable', 'receivable')
                    and r.date_maturity <= cutoff_date
                    )):
                amount = abs(move_line.debit - move_line.credit)
                total_amount += amount
                for partial_line in move_line.matched_debit_ids:
                    total_reconciled += partial_line.amount
                for partial_line in move_line.matched_credit_ids:
                    total_reconciled += partial_line.amount
            values = {
                'residual': residual,
                'residual_due': total_amount - total_reconciled,
                'difference': residual - (line.amount or 0.0),
                'partner_id': invoice.partner_id.id,
            }
            line.update(values)

    @api.onchange('amount')
    def _onchange_amount(self):
        for line in self:
            line.difference = line.residual - line.amount
