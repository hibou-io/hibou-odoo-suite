# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

"""
Patched because other modules may extend original functions.
"""

from odoo.addons.account.models import account_payment


def post(self):
    """ Create the journal items for the payment and update the payment's state to 'posted'.
        A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
        and another in the destination reconcilable account (see _compute_destination_account_id).
        If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
        If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
    """
    """
    Manual Payment Disperse functionality:
    During reconciliation, reconcile specific lines to specific invoices so that the invoices 
    are paid down in the desired way.
    """
    register_wizard = None
    if self._context.get('payment_wizard_id'):
        register_wizard = self.env['account.payment.register'].browse(self._context.get('payment_wizard_id')).exists()
    is_manual_disperse = bool(register_wizard and register_wizard.is_manual_disperse)

    AccountMove = self.env['account.move'].with_context(default_type='entry')
    for rec in self:

        if rec.state != 'draft':
            raise UserError(_("Only a draft payment can be posted."))

        if any(inv.state != 'posted' for inv in rec.invoice_ids):
            raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

        # keep the name in case of a payment reset to draft
        if not rec.name:
            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
            if not rec.name and rec.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

        moves = AccountMove.create(rec._prepare_payment_moves())
        moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

        # Update the state / move before performing any reconciliation.
        move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
        rec.write({'state': 'posted', 'move_name': move_name})

        if rec.payment_type in ('inbound', 'outbound'):
            # ==== 'inbound' / 'outbound' ====
            if is_manual_disperse:
                move = moves[0]
                digits_rounding_precision = move.company_id.currency_id.rounding
                # pick out lines...
                for i in register_wizard.payment_invoice_ids:
                    i_values = rec._values_for_payment_invoice_line(i, None)
                    if not any((i_values['debit'], i_values['credit'])):
                        continue
                    move_line = move.line_ids.filtered(lambda l: not l.reconciled and l.account_id == rec.destination_account_id and l.account_id != l.payment_id.writeoff_account_id and
                                                                 float_is_zero(l.debit - i_values['debit'], precision_rounding=digits_rounding_precision) and
                                                                 float_is_zero(l.credit - i_values['credit'], precision_rounding=digits_rounding_precision))
                    i_lines = i.invoice_id.line_ids.filtered(lambda l: not l.reconciled and l.account_id == rec.destination_account_id)
                    if move_line and i_lines:
                        (move_line + i_lines).reconcile()
            else:
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label))\
                        .reconcile()
        elif rec.payment_type == 'transfer':
            # ==== 'transfer' ====
            moves.mapped('line_ids')\
                .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                .reconcile()

    return True


def _prepare_payment_moves(self):
    ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
    to the 'create' method.

    Example 1: outbound with write-off:

    Account             | Debit     | Credit
    ---------------------------------------------------------
    BANK                |   900.0   |
    RECEIVABLE          |           |   1000.0
    WRITE-OFF ACCOUNT   |   100.0   |

    Example 2: internal transfer from BANK to CASH:

    Account             | Debit     | Credit
    ---------------------------------------------------------
    BANK                |           |   1000.0
    TRANSFER            |   1000.0  |
    CASH                |   1000.0  |
    TRANSFER            |           |   1000.0

    :return: A list of Python dictionary to be passed to env['account.move'].create.
    '''
    """
    Manual Payment Disperse functionality:
    During journal entry creation, create a single line per invoice for the amount
    to be paid on that invoice.
    However, all write-offs are accumulated on a single line.
    """
    register_wizard = None
    if self._context.get('payment_wizard_id'):
        register_wizard = self.env['account.payment.register'].browse(
            self._context.get('payment_wizard_id')).exists()
    is_manual_disperse = bool(register_wizard and register_wizard.is_manual_disperse)

    all_move_vals = []
    for payment in self:
        company_currency = payment.company_id.currency_id
        move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

        # Compute amounts.
        write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
        # Manual Disperse
        if is_manual_disperse:
            write_off_amount = sum(register_wizard.payment_invoice_ids.filtered(
                lambda l: l.close_balance and l.difference and l.invoice_id in payment.invoice_ids).mapped('difference'))
            if payment.payment_type == 'outbound':
                write_off_amount *= -1.0

        if payment.payment_type in ('outbound', 'transfer'):
            counterpart_amount = payment.amount
            liquidity_line_account = payment.journal_id.default_debit_account_id
        else:
            counterpart_amount = -payment.amount
            liquidity_line_account = payment.journal_id.default_credit_account_id

        # Manage currency.
        if payment.currency_id == company_currency:
            # Single-currency.
            balance = counterpart_amount
            write_off_balance = write_off_amount
            counterpart_amount = write_off_amount = 0.0
            currency_id = False
        else:
            # Multi-currencies.
            balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
            write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
            currency_id = payment.currency_id.id

        # Manage custom currency on journal for liquidity line.
        if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
            # Custom currency on journal.
            if payment.journal_id.currency_id == company_currency:
                # Single-currency
                liquidity_line_currency_id = False
            else:
                liquidity_line_currency_id = payment.journal_id.currency_id.id
            liquidity_amount = company_currency._convert(
                balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
        else:
            # Use the payment currency.
            liquidity_line_currency_id = currency_id
            liquidity_amount = counterpart_amount

        # Compute 'name' to be used in receivable/payable line.
        rec_pay_line_name = ''
        if payment.payment_type == 'transfer':
            rec_pay_line_name = payment.name
        else:
            if payment.partner_type == 'customer':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Customer Payment")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Customer Credit Note")
            elif payment.partner_type == 'supplier':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Vendor Credit Note")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Vendor Payment")
            if payment.invoice_ids:
                rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

        # Compute 'name' to be used in liquidity line.
        if payment.payment_type == 'transfer':
            liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
        else:
            liquidity_line_name = payment.name

        # ==== 'inbound' / 'outbound' ====

        move_vals = {
            'date': payment.payment_date,
            'ref': payment.communication,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
            'partner_id': payment.partner_id.id,
            'line_ids': [
                # Receivable / Payable / Transfer line.
                # (0, 0, {
                #     'name': rec_pay_line_name,
                #     'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                #     'currency_id': currency_id,
                #     'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                #     'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                #     'date_maturity': payment.payment_date,
                #     'partner_id': payment.partner_id.commercial_partner_id.id,
                #     'account_id': payment.destination_account_id.id,
                #     'payment_id': payment.id,
                # }),
                # Liquidity line.
                (0, 0, {
                    'name': liquidity_line_name,
                    'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                    'currency_id': liquidity_line_currency_id,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': liquidity_line_account.id,
                    'payment_id': payment.id,
                }),
            ],
        }

        if is_manual_disperse:
            for i in register_wizard.payment_invoice_ids.filtered(lambda l: l.invoice_id in payment.invoice_ids):
                i_rec_pay_line_name = rec_pay_line_name
                i_values = payment._values_for_payment_invoice_line(i, currency_id)
                if not any((i_values['debit'], i_values['credit'])):
                    # do not make useless lines
                    continue
                move_vals['line_ids'].insert(0, (0, 0, {
                    'name': i_rec_pay_line_name,
                    # 'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                    # 'amount_currency': i_amount_currency,
                    # 'currency_id': currency_id,
                    # # 'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                    # 'debit': i_amount if i_amount > 0.0 else 0.0,
                    # # 'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                    # 'credit': -i_amount if i_amount < 0.0 else 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.destination_account_id.id,
                    'payment_id': payment.id,
                    **i_values,
                }))
        else:
            # insert because existing tests expect them in a set order.
            move_vals['line_ids'].insert(0, (0, 0, {
                'name': rec_pay_line_name,
                'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                'currency_id': currency_id,
                'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                'date_maturity': payment.payment_date,
                'partner_id': payment.partner_id.commercial_partner_id.id,
                'account_id': payment.destination_account_id.id,
                'payment_id': payment.id,
            }))

        if write_off_balance:
            # Write-off line.
            move_vals['line_ids'].append((0, 0, {
                'name': payment.writeoff_label,
                'amount_currency': -write_off_amount,
                'currency_id': currency_id,
                'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                'date_maturity': payment.payment_date,
                'partner_id': payment.partner_id.commercial_partner_id.id,
                'account_id': payment.writeoff_account_id.id,
                'payment_id': payment.id,
            }))

        if move_names:
            move_vals['name'] = move_names[0]

        all_move_vals.append(move_vals)

        # ==== 'transfer' ====
        if payment.payment_type == 'transfer':
            journal = payment.destination_journal_id

            # Manage custom currency on journal for liquidity line.
            if journal.currency_id and payment.currency_id != journal.currency_id:
                # Custom currency on journal.
                liquidity_line_currency_id = journal.currency_id.id
                transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                transfer_amount = counterpart_amount

            transfer_move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'partner_id': payment.partner_id.id,
                'journal_id': payment.destination_journal_id.id,
                'line_ids': [
                    # Transfer debit line.
                    (0, 0, {
                        'name': payment.name,
                        'amount_currency': -counterpart_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.company_id.transfer_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity credit line.
                    (0, 0, {
                        'name': _('Transfer from %s') % payment.journal_id.name,
                        'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.destination_journal_id.default_credit_account_id.id,
                        'payment_id': payment.id,
                    }),
                ],
            }

            if move_names and len(move_names) == 2:
                transfer_move_vals['name'] = move_names[1]

            all_move_vals.append(transfer_move_vals)

    return all_move_vals


account_payment.account_payment.post = post
account_payment.account_payment._prepare_payment_moves = _prepare_payment_moves
