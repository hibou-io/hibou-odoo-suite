# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import _
from odoo.exceptions import UserError

"""
Patched because other modules may extend original functions.
"""

from odoo.addons.account.models import account_payment


def _synchronize_from_moves(self, changed_fields):
    ''' Update the account.payment regarding its related account.move.
    Also, check both models are still consistent.
    :param changed_fields: A set containing all modified fields on account.move.
    '''
    if self._context.get('skip_account_move_synchronization'):
        return

    for pay in self.with_context(skip_account_move_synchronization=True):

        # After the migration to 14.0, the journal entry could be shared between the account.payment and the
        # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
        if pay.move_id.statement_line_id:
            continue

        move = pay.move_id
        move_vals_to_write = {}
        payment_vals_to_write = {}

        if 'journal_id' in changed_fields:
            if pay.journal_id.type not in ('bank', 'cash'):
                raise UserError(_("A payment must always belongs to a bank or cash journal."))

        if 'line_ids' in changed_fields:
            all_lines = move.line_ids
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # PATCHED
            # if len(liquidity_lines) != 1:
            if len(liquidity_lines.account_id) != 1:
                raise UserError(_(
                    "Journal Entry %s is not valid. In order to proceed, the journal items must "
                    "include one and only one outstanding payments/receipts account.",
                    move.display_name,
                ))

            # PATCHED
            # if len(counterpart_lines) != 1:
            if len(counterpart_lines.account_id) != 1:
                raise UserError(_(
                    "Journal Entry %s is not valid. In order to proceed, the journal items must "
                    "include one and only one receivable/payable account (with an exception of "
                    "internal transfers).",
                    move.display_name,
                ))

            if writeoff_lines and len(writeoff_lines.account_id) != 1:
                raise UserError(_(
                    "Journal Entry %s is not valid. In order to proceed, "
                    "all optional journal items must share the same account.",
                    move.display_name,
                ))

            if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                raise UserError(_(
                    "Journal Entry %s is not valid. In order to proceed, the journal items must "
                    "share the same currency.",
                    move.display_name,
                ))

            if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                raise UserError(_(
                    "Journal Entry %s is not valid. In order to proceed, the journal items must "
                    "share the same partner.",
                    move.display_name,
                ))

            if counterpart_lines.account_id.user_type_id.type == 'receivable':
                partner_type = 'customer'
            else:
                partner_type = 'supplier'

            liquidity_amount = liquidity_lines.amount_currency

            move_vals_to_write.update({
                'currency_id': liquidity_lines.currency_id.id,
                'partner_id': liquidity_lines.partner_id.id,
            })
            payment_vals_to_write.update({
                'amount': abs(liquidity_amount),
                'partner_type': partner_type,
                'currency_id': liquidity_lines.currency_id.id,
                'destination_account_id': counterpart_lines.account_id.id,
                'partner_id': liquidity_lines.partner_id.id,
            })
            if liquidity_amount > 0.0:
                payment_vals_to_write.update({'payment_type': 'inbound'})
            elif liquidity_amount < 0.0:
                payment_vals_to_write.update({'payment_type': 'outbound'})

        move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
        pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))
  
account_payment.AccountPayment._synchronize_from_moves = _synchronize_from_moves
