from odoo import api, Command, fields, models


class Payslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model_create_multi
    def create(self, vals_list):
        payslips = super().create(vals_list)
        draft_slips = payslips.filtered(lambda p: p.employee_id and p.state == 'draft')
        if not draft_slips:
            return payslips
        
        draft_slips._update_badges()
        return payslips
    
    def write(self, vals):
        res = super().write(vals)
        if 'date_to' in vals or 'date_from' in vals:
            self._update_badges()
        return res

    def _update_badges(self):
        badge_type = self.env.ref('hr_payroll_gamification.badge_other_input', raise_if_not_found=False)
        if not badge_type:
            return
        for payslip in self:
            amount = payslip._get_input_badge_amount()
            line = payslip.input_line_ids.filtered(lambda l: l.input_type_id == badge_type)
            command = []
            if line and not amount:
                command.append((2, line.id, False))
            elif line and amount:
                command.append((1, line.id, {
                    'amount': amount,
                }))
            elif amount:
                command.append((0, 0, {
                    'name': badge_type.name,
                    'amount': amount,
                    'input_type_id': badge_type.id,
                }))
            if command:
                payslip.update({'input_line_ids': command})

    def _get_input_badge_amount(self):
        amount = 0.0
        for bu in self.employee_id.badge_ids.filtered(lambda bu: bu.badge_id.payroll_type == 'fixed'):
            amount += bu.badge_id.payroll_amount
        for bu in self.employee_id.badge_ids.filtered(lambda bu: (
                bu.badge_id.payroll_type == 'period'
                and self.date_from <= bu.create_date.date() <= self.date_to
        )):
            amount += bu.badge_id.payroll_amount
        return amount
