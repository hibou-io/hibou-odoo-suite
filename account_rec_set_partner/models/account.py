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
    def _apply_rules(self, st_line, partner):
        ''' Apply criteria to get candidates for all reconciliation models.

        This function is called in enterprise by the reconciliation widget to match
        the statement line with the available candidates (using the reconciliation models).

        :param st_line: The statement line to match.
        :param partner: The partner to consider.
        :return:        A dict mapping each statement line id with:
            * aml_ids:          A list of account.move.line ids.
            * model:            An account.reconcile.model record (optional).
            * status:           'reconciled' if the lines has been already reconciled, 'write_off' if the write-off
                                must be applied on the statement line.
            * auto_reconcile:   A flag indicating if the match is enough significant to auto reconcile the candidates.
        '''
        available_models = self.filtered(lambda m: m.rule_type != 'writeoff_button').sorted()

        for rec_model in available_models:

            if not rec_model._is_applicable_for(st_line, partner):
                continue

            if rec_model.rule_type == 'invoice_matching':
                rules_map = rec_model._get_invoice_matching_rules_map()
                for rule_index in sorted(rules_map.keys()):
                    for rule_method in rules_map[rule_index]:
                        candidate_vals = rule_method(st_line, partner)
                        if not candidate_vals:
                            continue

                        if candidate_vals.get('amls'):
                            res = rec_model._get_invoice_matching_amls_result(st_line, partner, candidate_vals)
                            if res:
                                return {
                                    **res,
                                    'model': rec_model,
                                }
                        else:
                            return {
                                **candidate_vals,
                                'model': rec_model,
                            }

            elif rec_model.rule_type == 'writeoff_suggestion':
                # customize
                if rec_model.set_partner_id and not st_line.partner_id:
                    st_line.partner_id = rec_model.set_partner_id
                return {
                    'model': rec_model,
                    'status': 'write_off',
                    'auto_reconcile': rec_model.auto_reconcile,
                }
                # end customize
        return {}
