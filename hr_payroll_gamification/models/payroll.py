from odoo import api, Command, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id')
    def _compute_input_line_ids(self):
        res = super()._compute_input_line_ids()
        badge_type = self.env.ref('hr_payroll_gamification.badge_other_input', raise_if_not_found=False)
        if not badge_type:
            return res
        for slip in self:
            amount = slip._get_input_badges()
            if not amount:
                continue
            slip.update({
                'input_line_ids': [
                    Command.create({
                        'name': badge_type.name or 'Badges',
                        'amount': amount,
                        'input_type_id': badge_type.id,
                    }),
                ],
            })
        return res

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
