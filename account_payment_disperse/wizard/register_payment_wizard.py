# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.payment.register'

    is_manual_disperse = fields.Boolean(string='Disperse Manually')
    payment_invoice_ids = fields.One2many('account.payment.register.payment_invoice', 'wizard_id', string='Invoices')
    payment_difference_handling = fields.Selection(compute='_compute_payment_difference_handling', store=True, readonly=False)
    due_date_cutoff = fields.Date(string='Due Date Cutoff', default=fields.Date.today)
    due_date_behavior = fields.Selection([
        ('due', 'Due'),
        ('next_due', 'Next Due'),
    ], string='Due Date Behavior', default='due')

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountRegisterPayments, self).default_get(default_fields)
        if 'line_ids' in rec:
            lines = self.env['account.move.line'].browse(rec['line_ids'][0][2])
            if lines:
                rec['payment_invoice_ids'] = [fields.Command.create({'invoice_id': i}) for i in lines.move_id.ids]
        return rec
    
    @api.onchange('is_manual_disperse')
    def _ensure_is_grouped(self):
        for wizard in self.filtered('is_manual_disperse'):
            wizard.group_payment = True
            
    @api.onchange('group_payment')
    def _ensure_is_not_manual(self):
        for wizard in self.filtered(lambda w: not w.group_payment):
            wizard.is_manual_disperse = False

    @api.depends('payment_invoice_ids.close_balance')
    def _compute_payment_difference_handling(self):
        for wizard in self:
            if any(wizard.payment_invoice_ids.mapped('close_balance')):
                wizard.payment_difference_handling = 'reconcile'
            else:
                wizard.payment_difference_handling =  'open'

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'is_manual_disperse', 'payment_invoice_ids.amount')
    def _compute_amount(self):
        is_manual = self.filtered(lambda p: p.is_manual_disperse)
        super(AccountRegisterPayments, self - is_manual)._compute_amount()
        for wizard in is_manual:
            wizard.amount = sum(wizard.mapped('payment_invoice_ids.amount') or [0.0])
            
    def _create_payment_vals_from_wizard(self):
        res = super(AccountRegisterPayments, self)._create_payment_vals_from_wizard()
        if self.is_manual_disperse:
            write_off_line_vals = res.get('write_off_line_vals')
            if write_off_line_vals:
                write_off_line_vals['amount'] = sum(self.payment_invoice_ids.filtered('close_balance').mapped('difference'))
            res['line_ids'] = self._create_payment_line_vals(
                write_off_line_vals=write_off_line_vals,
            )
        return res
    
    def _create_payment_line_vals(self, write_off_line_vals=None):
        write_off_line_vals = write_off_line_vals or {}
        
        outstanding_account_id = self._get_outstanding_account_id()
        if not outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))
        
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0
        
        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )    
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )

        # Compute a default label to set on the journal items.

        payment_display_name = self.env['account.payment']._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.payment_date,
            partner=self.partner_id,
        )
        
        line_vals_list = [
            # Liquidity line.
            {
                'name': default_line_name,
                'date_maturity': self.payment_date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': self.currency_id.id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': outstanding_account_id,
            },
        ]
        for line in self.payment_invoice_ids.filtered(lambda l: not self.currency_id.is_zero(l.amount) 
                                                                or l.close_balance):
            # Receivable / Payable.
            line_vals_list.append({
                'name': default_line_name,
                'date_maturity': self.payment_date,
                # 'amount_currency': counterpart_amount_currency,
                # 'currency_id': self.currency_id.id,
                # 'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                # 'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.line_ids[0].account_id.id,
                **line._values_for_payment_invoice_line()
            })
        if not self.currency_id.is_zero(write_off_amount_currency):
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': self.currency_id.id,
                'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return [fields.Command.create(line_vals) for line_vals in line_vals_list]
    
    def _get_outstanding_account_id(self):
        outstanding_account_id = False
        if self.payment_type == 'inbound':
                outstanding_account_id = (self.payment_method_line_id.payment_account_id
                                              or self.journal_id.company_id.account_journal_payment_debit_account_id)
        elif self.payment_type == 'outbound':
            outstanding_account_id = (self.payment_method_line_id.payment_account_id
                                            or self.journal_id.company_id.account_journal_payment_credit_account_id)
        return outstanding_account_id and outstanding_account_id.id
    
    def _reconcile_payments(self, to_process, edit_mode=False):
        if self.is_manual_disperse:
            domain = [
                ('parent_state', '=', 'posted'),
                ('account_internal_type', 'in', ('receivable', 'payable')),
                ('reconciled', '=', False),
            ]
            for vals in to_process:
                # account_id = vals['batch']['payment_values']['account_id']
                payment = vals['payment']
                account = payment.destination_account_id
                payment_lines = vals['payment'].line_ids.filtered_domain(domain)
                move_lines = vals['to_reconcile']
                currency = self.company_id.currency_id

                for disperse_line in self.payment_invoice_ids.filtered(lambda l: l.invoice_id in move_lines.move_id):
                    line_values = disperse_line._values_for_payment_invoice_line()
                    lines_to_reconcile = payment_lines.filtered(
                        lambda l: l.account_id == account 
                                and not l.reconciled
                                and currency.is_zero(l.debit - line_values['debit'])
                                and currency.is_zero(l.credit - line_values['credit'])
                    )
                    lines_to_reconcile |= move_lines.filtered(
                        lambda l: l.account_id == account 
                                and not l.reconciled
                                and l.move_id == disperse_line.invoice_id
                    )
                    lines_to_reconcile.reconcile()
        else:
            super(AccountRegisterPayments, self)._reconcile_payments(to_process, edit_mode=edit_mode)

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
            'view_id': self.env.ref('account.view_account_payment_register_form').id,
            'context': self.env.context,
            'target': 'new',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }


class AccountRegisterPaymentsInvoiceLine(models.TransientModel):
    _name = 'account.payment.register.payment_invoice'
    _description = 'Register Payment Invoice'

    wizard_id = fields.Many2one('account.payment.register')
    invoice_id = fields.Many2one('account.move', string='Invoice', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', compute='_compute_invoice_balances', compute_sudo=True)
    residual = fields.Float(string='Remaining', compute='_compute_invoice_balances', compute_sudo=True)
    residual_due = fields.Float(string='Due', compute='_compute_invoice_balances', compute_sudo=True)
    difference = fields.Float(string='Difference', compute='_compute_difference')
    amount = fields.Float(string='Amount')
    close_balance = fields.Boolean(string='Close Balance', help='Write off remaining balance.')

    @api.depends('invoice_id', 'wizard_id.due_date_cutoff', 'wizard_id.due_date_behavior', 'invoice_id.partner_id', 'wizard_id.currency_id', 'wizard_id.company_id')
    def _compute_invoice_balances(self):
        dummy_date = datetime(1980, 1, 1)
        for line in self:
            invoice = line.invoice_id.browse(line.invoice_id.id)
            sign = 1.0 if invoice.move_type in ('out_invoice', 'out_refund') else -1.0
            residual = sign * invoice.amount_residual_signed

            cutoff_date = line.wizard_id.due_date_cutoff
            due_behavior = line.wizard_id.due_date_behavior
            total_amount = 0.0
            total_reconciled = 0.0

            if due_behavior == 'due':
                for move_line in invoice.line_ids.filtered(lambda r: (
                        not r.reconciled
                        and r.account_id.internal_type in ('payable', 'receivable')
                        and (not r.date_maturity or r.date_maturity <= cutoff_date)
                        )):
                    amount = move_line.debit - move_line.credit
                    total_amount += amount
                    for partial_line in move_line.matched_debit_ids:
                        total_reconciled -= partial_line.amount
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
                        total_reconciled -= partial_line.amount
                    for partial_line in move_line.matched_credit_ids:
                        total_reconciled += partial_line.amount
            if self.wizard_id.currency_id:
                residual = invoice.company_id.currency_id._convert(
                    residual,
                    self.wizard_id.currency_id,
                    self.wizard_id.company_id,
                    self.wizard_id.payment_date,
                )
                total_amount = invoice.company_id.currency_id._convert(
                    total_amount,
                    self.wizard_id.currency_id,
                    self.wizard_id.company_id,
                    self.wizard_id.payment_date,
                )
                total_reconciled = invoice.company_id.currency_id._convert(
                    total_reconciled,
                    self.wizard_id.currency_id,
                    self.wizard_id.company_id,
                    self.wizard_id.payment_date,
                )
            values = {
                'residual': residual,
                'residual_due': sign * (total_amount - total_reconciled),
                'partner_id': invoice.partner_id.id,
            }
            line.update(values)

    @api.depends('amount', 'residual', 'residual_due', 'invoice_id')
    def _compute_difference(self):
        for line in self:
            line.difference = line.residual - line.amount
            
    def _values_for_payment_invoice_line(self):
        self.ensure_one()
        
        sign = 1.0 if self.wizard_id.payment_type == 'outbound' else -1.0
        i_write_off_amount = self.difference if self.difference and self.close_balance else 0.0
        i_amount_currency = (self.amount + i_write_off_amount)
        i_amount = sign * self.wizard_id.currency_id._convert(
            i_amount_currency,
            self.wizard_id.company_id.currency_id,
            self.wizard_id.company_id,
            self.wizard_id.payment_date,
        )
        return {
            'amount_currency': sign * i_amount_currency,
            'currency_id': self.wizard_id.currency_id.id,
            'debit': i_amount if i_amount > 0.0 else 0.0,
            'credit': -i_amount if i_amount < 0.0 else 0.0,
        }
