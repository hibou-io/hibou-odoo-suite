from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero
from collections import defaultdict


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

        This function is called in enterprise by the reconciliation widget to match
        the statement lines with the available candidates (using the reconciliation models).

        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                A dict mapping each statement line id with:
            * aml_ids:      A list of account.move.line ids.
            * model:        An account.reconcile.model record (optional).
            * status:       'reconciled' if the lines has been already reconciled, 'write_off' if the write-off must be
                            applied on the statement line.
        '''
        # This functions uses SQL to compute its results. We need to flush before doing anything more.
        for model_name in ('account.bank.statement', 'account.bank.statement.line', 'account.move', 'account.move.line', 'res.company', 'account.journal', 'account.account'):
            self.env[model_name].flush(self.env[model_name]._fields)

        results = {line.id: {'aml_ids': []} for line in st_lines}

        available_models = self.filtered(lambda m: m.rule_type != 'writeoff_button').sorted()
        aml_ids_to_exclude = set() # Keep track of already processed amls.
        reconciled_amls_ids = set() # Keep track of already reconciled amls.

        # First associate with each rec models all the statement lines for which it is applicable
        lines_with_partner_per_model = defaultdict(lambda: [])
        for st_line in st_lines:

            # Statement lines created in old versions could have a residual amount of zero. In that case, don't try to
            # match anything.
            if not st_line.amount_residual:
                continue

            mapped_partner = (partner_map and partner_map.get(st_line.id) and self.env['res.partner'].browse(partner_map[st_line.id])) or st_line.partner_id

            for rec_model in available_models:
                partner = mapped_partner or rec_model._get_partner_from_mapping(st_line)

                if rec_model._is_applicable_for(st_line, partner):
                    # Customization
                    if not partner and rec_model.set_partner_id and not rec_model.match_partner:
                        partner = rec_model.set_partner_id
                        st_line.partner_id = partner
                    # End Customization

                    lines_with_partner_per_model[rec_model].append((st_line, partner))

        # Execute only one SQL query for each model (for performance)
        matched_lines = self.env['account.bank.statement.line']
        for rec_model in available_models:

            # We filter the lines for this model, in case a previous one has already found something for them
            filtered_st_lines_with_partner = [x for x in lines_with_partner_per_model[rec_model] if x[0] not in matched_lines]

            if not filtered_st_lines_with_partner:
                # No unreconciled statement line for this model
                continue

            all_model_candidates = rec_model._get_candidates(filtered_st_lines_with_partner, excluded_ids)

            for st_line, partner in filtered_st_lines_with_partner:
                candidates = all_model_candidates[st_line.id]
                if candidates:
                    model_rslt, new_reconciled_aml_ids, new_treated_aml_ids = rec_model._get_rule_result(st_line, candidates, aml_ids_to_exclude, reconciled_amls_ids, partner)

                    if model_rslt:
                        # We inject the selected partner (possibly coming from the rec model)
                        model_rslt['partner']= partner

                        results[st_line.id] = model_rslt
                        reconciled_amls_ids |= new_reconciled_aml_ids
                        aml_ids_to_exclude |= new_treated_aml_ids
                        matched_lines += st_line

        return results
