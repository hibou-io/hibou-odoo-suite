from odoo import api, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super()._onchange_employee()
        if self.state == 'draft':
            self._input_badges()
        return res

    def _input_badges(self):
        badge_type = self.env.ref('hr_payroll_gamification.badge_other_input', raise_if_not_found=False)
        if not badge_type:
            return

        amount = self._get_input_badges()
        if not amount:
            return

        lines_to_keep = self.input_line_ids.filtered(lambda x: x.input_type_id != badge_type)
        input_lines_vals = [(5, 0, 0)] + [(4, line.id, False) for line in lines_to_keep]
        input_lines_vals.append((0, 0, {
            'amount': amount,
            'input_type_id': badge_type,
        }))
        self.update({'input_line_ids': input_lines_vals})

    def _get_input_badges(self):
        amount = 0.0
        for bu in self.employee_id.badge_ids.filtered(lambda bu: bu.badge_id.payroll_type == 'fixed'):
            amount += bu.badge_id.payroll_amount
        for bu in self.employee_id.badge_ids.filtered(lambda bu: (
                bu.badge_id.payroll_type == 'period'
                and self.date_from <= bu.create_date.date() <= self.date_to
        )):
            amount += bu.badge_id.payroll_amount
        return amount
