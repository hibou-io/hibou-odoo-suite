from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _create_payment_entry(self, amount):
        wizard_id = self.env.context.get('payment_wizard_id')
        if wizard_id:
            wizard = self.env['account.register.payments'].browse(wizard_id)
            assert wizard
            if wizard.is_manual_disperse:
                payment_amount = sum(wizard.invoice_line_ids.filtered(lambda p: p.partner_id == self.partner_id).mapped('amount'))
                if amount < 0:
                    payment_amount = -payment_amount
                return self._create_payment_entry_manual_disperse(payment_amount, wizard)

        return super(AccountPayment, self)._create_payment_entry(amount)

    def _create_payment_entry_manual_disperse(self, amount, wizard):
        # When registering payments for multiple partners at the same time, without setting
        # the amount again, then the payment will not match the accounting.
        self.amount = abs(amount)
        if hasattr(self, 'check_amount_in_words'):
            self.check_amount_in_words = self.currency_id.amount_to_text(self.amount)

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        inv_lines = []
        for partial_invoice in wizard.invoice_line_ids.filtered(lambda p: p.amount and p.partner_id == self.partner_id):
            # Note that for customer payments, the amount will be reversed.
            inv_amount = partial_invoice.amount if amount > 0 else -partial_invoice.amount
            i_debit, i_credit, i_amount_currency, i_currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(inv_amount, self.currency_id, self.company_id.currency_id)
            counterpart_aml_dict = self._get_shared_move_line_vals(i_debit, i_credit, i_amount_currency, move.id, False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(partial_invoice.invoice_id))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)
            counterpart_aml |= partial_invoice.invoice_id.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            inv_lines.append((counterpart_aml, partial_invoice.writeoff_acc_id))

        # Useful for debugging
        # for aml_ids, writeoff_acc_id in inv_lines:
        #     _logger.warn('pair:' + (' writeoff: ' + str(writeoff_acc_id)) if writeoff_acc_id else '')
        #     for l in aml_ids:
        #         _logger.warn('    ' + str(l) + ' debit: ' + str(l.debit) + ' credit: ' + str(l.credit))

        # Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            other = aml_obj.create(liquidity_aml_dict)
            #_logger.warn('other line -- debit: ' + str(other.debit) + ' credit: ' + str(other.credit))

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        for aml_ids, writeoff_acc_id in inv_lines:
            aml_ids.reconcile(writeoff_acc_id, wizard.writeoff_journal_id)

        return move
