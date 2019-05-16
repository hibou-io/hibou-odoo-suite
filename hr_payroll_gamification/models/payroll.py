from odoo import api, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(Payslip, self).get_inputs(contracts, date_from, date_to)
        for contract in contracts:
            for input in res:
                if input.get('code') == 'BADGES':
                    input['amount'] = self._get_input_badges(contract, date_from, date_to)
        return res

    def _get_input_badges(self, contract, date_from, date_to):
        return sum(contract.employee_id.badge_ids.filtered(lambda l: l.badge_id.payroll_type == 'fixed').mapped('badge_id.payroll_amount'))
