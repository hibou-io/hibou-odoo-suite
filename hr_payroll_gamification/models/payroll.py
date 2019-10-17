from odoo import api, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(Payslip, self).get_inputs(contracts, date_from, date_to)
        for contract in contracts:
            for input in res:
                if input.get('contract_id') == contract.id and input.get('code') == 'BADGES':
                    input['amount'] = self._get_input_badges(contract, date_from, date_to)
        return res

    def _get_input_badges(self, contract, date_from, date_to):
        amount = 0.0
        for bu in contract.employee_id.badge_ids.filtered(lambda bu: bu.badge_id.payroll_type == 'fixed'):
            amount += bu.badge_id.payroll_amount
        for bu in contract.employee_id.badge_ids.filtered(lambda bu: (
                bu.badge_id.payroll_type == 'period'
                and date_from <= bu.create_date.date() <= date_to
        )):
            amount += bu.badge_id.payroll_amount
        return amount
