from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class AccountReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    set_partner_id = fields.Many2one('res.partner', string='Set Partner')

    """
    Big override/patch to extend the behavior during proposal of 
    write off if the rule has a "set_partner_id" and the statement
    line does not have a partner set.
    """
    def _apply_rules(self, st_lines, excluded_ids=None, partner_map=None):
        ''' Apply criteria to get candidates for all reconciliation models.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                A dict mapping each statement line id with:
            * aml_ids:      A list of account.move.line ids.
            * model:        An account.reconcile.model record (optional).
            * status:       'reconciled' if the lines has been already reconciled, 'write_off' if the write-off must be
                            applied on the statement line.
        '''
        available_models = self.filtered(lambda m: m.rule_type != 'writeoff_button')

        results = dict((r.id, {'aml_ids': []}) for r in st_lines)

        if not available_models:
            return results

        ordered_models = available_models.sorted(key=lambda m: (m.sequence, m.id))

        grouped_candidates = {}

        # Type == 'invoice_matching'.
        # Map each (st_line.id, model_id) with matching amls.
        invoices_models = ordered_models.filtered(lambda m: m.rule_type == 'invoice_matching')
        self.env['account.move'].flush(['state'])
        self.env['account.move.line'].flush(['balance', 'reconciled'])
        self.env['account.bank.statement.line'].flush(['company_id'])
        if invoices_models:
            query, params = invoices_models._get_invoice_matching_query(st_lines, excluded_ids=excluded_ids, partner_map=partner_map)
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()

            for res in query_res:
                grouped_candidates.setdefault(res['id'], {})
                grouped_candidates[res['id']].setdefault(res['model_id'], [])
                grouped_candidates[res['id']][res['model_id']].append(res)

        # Type == 'writeoff_suggestion'.
        # Map each (st_line.id, model_id) with a flag indicating the st_line matches the criteria.
        write_off_models = ordered_models.filtered(lambda m: m.rule_type == 'writeoff_suggestion')
        if write_off_models:
            query, params = write_off_models._get_writeoff_suggestion_query(st_lines, excluded_ids=excluded_ids, partner_map=partner_map)
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()

            for res in query_res:
                grouped_candidates.setdefault(res['id'], {})
                grouped_candidates[res['id']].setdefault(res['model_id'], True)

        # Keep track of already processed amls.
        amls_ids_to_exclude = set()

        # Keep track of already reconciled amls.
        reconciled_amls_ids = set()

        # Iterate all and create results.
        for line in st_lines:
            line_currency = line.currency_id or line.journal_id.currency_id or line.company_id.currency_id
            line_residual = line.currency_id and line.amount_currency or line.amount

            # Search for applicable rule.
            # /!\ BREAK are very important here to avoid applying multiple rules on the same line.
            for model in ordered_models:
                # No result found.
                if not grouped_candidates.get(line.id) or not grouped_candidates[line.id].get(model.id):
                    continue

                if model.rule_type == 'invoice_matching':
                    candidates = grouped_candidates[line.id][model.id]

                    # If some invoices match on the communication, suggest them.
                    # Otherwise, suggest all invoices having the same partner.
                    # N.B: The only way to match a line without a partner is through the communication.
                    first_batch_candidates = []
                    first_batch_candidates_proposed = []
                    second_batch_candidates = []
                    second_batch_candidates_proposed = []
                    third_batch_candidates = []
                    third_batch_candidates_proposed = []
                    for c in candidates:
                        # Don't take into account already reconciled lines.
                        if c['aml_id'] in reconciled_amls_ids:
                            continue

                        # Dispatch candidates between lines matching invoices with the communication or only the partner.
                        elif c['payment_reference_flag']:
                            if c['aml_id'] in amls_ids_to_exclude:
                                first_batch_candidates_proposed.append(c)
                            else:
                                first_batch_candidates.append(c)
                        elif c['communication_flag']:
                            if c['aml_id'] in amls_ids_to_exclude:
                                second_batch_candidates_proposed.append(c)
                            else:
                                second_batch_candidates.append(c)
                        elif not first_batch_candidates:
                            if c['aml_id'] in amls_ids_to_exclude:
                                third_batch_candidates_proposed.append(c)
                            else:
                                third_batch_candidates.append(c)
                    available_candidates = (first_batch_candidates + first_batch_candidates_proposed
                                            or second_batch_candidates + second_batch_candidates_proposed
                                            or third_batch_candidates + third_batch_candidates_proposed)

                    # Special case: the amount are the same, submit the line directly.
                    for c in available_candidates:
                        residual_amount = c['aml_currency_id'] and c['aml_amount_residual_currency'] or c['aml_amount_residual']

                        if float_is_zero(residual_amount - line_residual, precision_rounding=line_currency.rounding):
                            available_candidates = [c]
                            break

                    # Needed to handle check on total residual amounts.
                    if first_batch_candidates or first_batch_candidates_proposed or model._check_rule_propositions(line, available_candidates):
                        results[line.id]['model'] = model

                        # Add candidates to the result.
                        for candidate in available_candidates:
                            results[line.id]['aml_ids'].append(candidate['aml_id'])
                            amls_ids_to_exclude.add(candidate['aml_id'])

                        # Create write-off lines.
                        move_lines = self.env['account.move.line'].browse(results[line.id]['aml_ids'])
                        partner = partner_map and partner_map.get(line.id) and self.env['res.partner'].browse(partner_map[line.id])

                        # Customization
                        if not partner and model.set_partner_id and not model.match_partner:
                            partner = model.set_partner_id
                            line.partner_id = partner
                        # End Customization

                        reconciliation_results = model._prepare_reconciliation(line, move_lines, partner=partner)

                        # A write-off must be applied.
                        if reconciliation_results['new_aml_dicts']:
                            results[line.id]['status'] = 'write_off'

                        # Process auto-reconciliation.
                        if (first_batch_candidates or second_batch_candidates) and model.auto_reconcile:
                            # An open balance is needed but no partner has been found.
                            if reconciliation_results['open_balance_dict'] is False:
                                break

                            new_aml_dicts = reconciliation_results['new_aml_dicts']
                            if reconciliation_results['open_balance_dict']:
                                new_aml_dicts.append(reconciliation_results['open_balance_dict'])
                            if not line.partner_id and partner:
                                line.partner_id = partner
                            counterpart_moves = line.process_reconciliation(
                                counterpart_aml_dicts=reconciliation_results['counterpart_aml_dicts'],
                                payment_aml_rec=reconciliation_results['payment_aml_rec'],
                                new_aml_dicts=new_aml_dicts,
                            )
                            results[line.id]['status'] = 'reconciled'
                            results[line.id]['reconciled_lines'] = counterpart_moves.mapped('line_ids')

                            # The reconciled move lines are no longer candidates for another rule.
                            reconciled_amls_ids.update(move_lines.ids)

                        # Break models loop.
                        break

                elif model.rule_type == 'writeoff_suggestion' and grouped_candidates[line.id][model.id]:
                    results[line.id]['model'] = model
                    results[line.id]['status'] = 'write_off'

                    # Create write-off lines.
                    partner = partner_map and partner_map.get(line.id) and self.env['res.partner'].browse(partner_map[line.id])
                    reconciliation_results = model._prepare_reconciliation(line, partner=partner)

                    # Customization
                    if not partner and model.set_partner_id and not model.match_partner:
                        partner = model.set_partner_id
                        line.partner_id = partner
                    # End Customization

                    if reconciliation_results['open_balance_dict'] is False:
                        break

                    # Process auto-reconciliation.
                    if model.auto_reconcile:
                        new_aml_dicts = reconciliation_results['new_aml_dicts']
                        if reconciliation_results['open_balance_dict']:
                            new_aml_dicts.append(reconciliation_results['open_balance_dict'])
                        if not line.partner_id and partner:
                            line.partner_id = partner
                        counterpart_moves = line.process_reconciliation(
                            counterpart_aml_dicts=reconciliation_results['counterpart_aml_dicts'],
                            payment_aml_rec=reconciliation_results['payment_aml_rec'],
                            new_aml_dicts=new_aml_dicts,
                        )
                        results[line.id]['status'] = 'reconciled'
                        results[line.id]['reconciled_lines'] = counterpart_moves.mapped('line_ids')

                    # Break models loop.
                    break
        return results
