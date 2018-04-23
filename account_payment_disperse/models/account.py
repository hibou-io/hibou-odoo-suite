from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _create_payment_entry(self, amount):
        wizard_id = self.env.context.get('payment_wizard_id')
        if wizard_id:
            wizard = self.env['account.register.payments'].browse(wizard_id)
            assert wizard
            if wizard.is_manual_disperse:
                return self._create_payment_entry_manual_disperse(
                    -sum(wizard.invoice_line_ids.filtered(lambda p: p.partner_id == self.partner_id).mapped('amount')),
                    wizard)

        return super(AccountPayment, self)._create_payment_entry(amount)

    def _create_payment_entry_manual_disperse(self, amount, wizard):
        self.amount = abs(amount)
        if hasattr(self, 'check_amount_in_words'):
            self.check_amount_in_words = self.currency_id.amount_to_text(self.amount)
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)\
            .compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        inv_lines = []
        for partial_invoice in wizard.invoice_line_ids.filtered(lambda p: p.amount and p.partner_id == self.partner_id):
            inv_amount = partial_invoice.amount if amount > 0 else -partial_invoice.amount
            i_debit, i_credit, i_amount_currency, i_currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(inv_amount, self.currency_id, self.company_id.currency_id,
                                                              invoice_currency)
            counterpart_aml_dict = self._get_shared_move_line_vals(i_debit, i_credit, i_amount_currency, move.id, False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(partial_invoice.invoice_id))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)
            # capture writeoff account etc.
            counterpart_aml |= partial_invoice.invoice_id.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
            inv_lines.append((counterpart_aml, partial_invoice.writeoff_acc_id))

        # Create Payment side (payment journal default accounts)
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        # validate the payment
        move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        for inv_lines, writeoff_acc_id in inv_lines:
            # _logger.warn('pair: ')
            # for l in inv_lines:
            #     _logger.warn('    ' + str(l) + ' credit: ' + str(l.credit) + ' debit: ' + str(l.debit))
            inv_lines.reconcile(writeoff_acc_id, wizard.writeoff_journal_id)

        return move
