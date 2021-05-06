# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.payment.register'

    is_manual_disperse = fields.Boolean(string='Disperse Manually')
    payment_invoice_ids = fields.One2many('account.payment.register.payment_invoice', 'wizard_id', string='Invoices')
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", domain="[('deprecated', '=', False)]", copy=False)
    requires_writeoff_account = fields.Boolean(compute='_compute_requires_writeoff_account')
    amount = fields.Float(string='Amount', compute='_compute_amount')
    due_date_cutoff = fields.Date(string='Due Date Cutoff', default=fields.Date.today)
    due_date_behavior = fields.Selection([
        ('due', 'Due'),
        ('next_due', 'Next Due'),
    ], string='Due Date Behavior', default='due')

    @api.model
    def default_get(self, fields):
        rec = super(AccountRegisterPayments, self).default_get(fields)
        if 'invoice_ids' in rec:
            invoice_ids = rec['invoice_ids'][0][2]
            rec['payment_invoice_ids'] = [(0, 0, {'invoice_id': i}) for i in invoice_ids]
        return rec

    def create_payments(self):
        for payment in self.filtered(lambda p: not p.amount and p.invoice_ids):
            payment._compute_amount()
        for payment in self.filtered(lambda p: p.is_manual_disperse):
            line_amount = sum(payment.payment_invoice_ids.mapped('amount'))
            if abs(line_amount - payment.amount) >= 0.01:
                raise ValidationError('Cannot pay for %0.2f worth of invoices with %0.2f total.' %
                                      (line_amount, payment.amount))
            if not payment.writeoff_account_id and payment.payment_invoice_ids.filtered(lambda l: l.close_balance and l.difference):
                raise ValidationError('Closing balance will require a difference account.')
        new_self = self.with_context(payment_wizard_id=self.id)
        return super(AccountRegisterPayments, new_self).create_payments()

    @api.onchange('is_manual_disperse')
    def _ensure_is_manual_disperse(self):
        for payment in self:
            payment.group_payment = payment.is_manual_disperse

    @api.depends('payment_invoice_ids.amount', 'invoice_ids', 'journal_id', 'payment_date', 'is_manual_disperse')
    def _compute_amount(self):
        for payment in self.filtered(lambda p: p.is_manual_disperse):
            payment.amount = sum(payment.mapped('payment_invoice_ids.amount') or [0.0])
        for payment in self.filtered(lambda p: not p.is_manual_disperse):
            if payment.invoice_ids:
                payment.amount = self.env['account.payment']._compute_payment_amount(
                    payment.invoice_ids,
                    payment.invoice_ids[0].currency_id,
                    payment.journal_id,
                    payment.payment_date)
            else:
                payment.amount = 0.0

    @api.depends('payment_invoice_ids.difference', 'payment_invoice_ids.close_balance')
    def _compute_requires_writeoff_account(self):
        for payment in self:
            if payment.is_manual_disperse:
                payment.requires_writeoff_account = bool(payment.payment_invoice_ids.filtered(
                    lambda l: l.difference and l.close_balance))
            else:
                payment.requires_writeoff_account = False

    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''
        if self.is_manual_disperse:
            # this will already be positive for both invoice types unlink the below amount (abs)
            amount = sum(self.payment_invoice_ids.filtered(lambda l: l.invoice_id in invoices).mapped('amount'))
            sign = 1.0
            if invoices:
                invoice = invoices[0]
                sign = 1.0 if invoice.type in ('out_invoice', 'out_refund') else -1.0
        else:
            amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id,
                                                                         self.journal_id, self.payment_date)
            sign = 1.0 if amount > 0.0 else -1.0
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self._prepare_communication(invoices),
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': 'inbound' if sign > 0 else 'outbound',
            'amount': abs(amount),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
            'writeoff_account_id': self.writeoff_account_id.id,
        }
        return values

    def action_fill_residual(self):
        for payment in self:
            for line in payment.payment_invoice_ids:
                line.amount = line.residual
            return payment._reopen_action()

    def action_fill_residual_due(self):
        for payment in self:
            for line in payment.payment_invoice_ids:
                line.amount = line.residual_due
            return payment._reopen_action()

    def action_toggle_close_balance(self):
        for payment in self:
            for line in payment.payment_invoice_ids:
                line.close_balance = not line.close_balance
            return payment._reopen_action()

    def _reopen_action(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_form_multi').id,
            'context': self.env.context,
            'target': 'new',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }


class AccountRegisterPaymentsInvoiceLine(models.TransientModel):
    _name = 'account.payment.register.payment_invoice'

    wizard_id = fields.Many2one('account.payment.register')
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', compute='_compute_invoice_balances', compute_sudo=True)
    residual = fields.Float(string='Remaining', compute='_compute_invoice_balances', compute_sudo=True)
    residual_due = fields.Float(string='Due', compute='_compute_invoice_balances', compute_sudo=True)
    difference = fields.Float(string='Difference', compute='_compute_difference')
    amount = fields.Float(string='Amount')
    close_balance = fields.Boolean(string='Close Balance', help='Write off remaining balance.')

    @api.depends('invoice_id', 'wizard_id.due_date_cutoff', 'wizard_id.due_date_behavior', 'invoice_id.partner_id')
    def _compute_invoice_balances(self):
        dummy_date = datetime(1980, 1, 1)
        for line in self:
            invoice = line.invoice_id.browse(line.invoice_id.id)
            sign = 1.0 if invoice.type in ('out_invoice', 'out_refund') else -1.0
            residual = sign * invoice.amount_residual_signed

            cutoff_date = line.wizard_id.due_date_cutoff
            due_behavior = line.wizard_id.due_date_behavior
            total_amount = 0.0
            total_reconciled = 0.0
            # TODO partial reconcile will need sign check
            if due_behavior == 'due':
                for move_line in invoice.line_ids.filtered(lambda r: (
                        not r.reconciled
                        and r.account_id.internal_type in ('payable', 'receivable')
                        and (not r.date_maturity or r.date_maturity <= cutoff_date)
                        )):
                    amount = move_line.debit - move_line.credit
                    total_amount += amount
                    for partial_line in move_line.matched_debit_ids:
                        total_reconciled += partial_line.amount
                    for partial_line in move_line.matched_credit_ids:
                        total_reconciled += partial_line.amount
            else:
                move_lines = invoice.line_ids.filtered(lambda r: (
                        not r.reconciled
                        and r.account_id.internal_type in ('payable', 'receivable')
                        )).sorted(key=lambda r: r.date_maturity or dummy_date)
                if move_lines:
                    move_line = move_lines[0]
                    amount = move_line.debit - move_line.credit
                    total_amount += amount
                    for partial_line in move_line.matched_debit_ids:
                        total_reconciled += partial_line.amount
                    for partial_line in move_line.matched_credit_ids:
                        total_reconciled += partial_line.amount
            values = {
                'residual': residual,
                'residual_due': sign * (total_amount - total_reconciled),
                # 'difference': sign * ((line.amount or 0.0) - residual),
                'difference': (line.amount or 0.0) - residual,
                'partner_id': invoice.partner_id.id,
            }
            line.update(values)

    @api.depends('amount', 'residual', 'residual_due', 'invoice_id')
    def _compute_difference(self):
        for line in self:
            line.difference = line.amount - line.residual
