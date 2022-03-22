# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, Command, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    commission_payment_ids = fields.One2many(
        'hr.commission.payment', 'payslip_id', string='Commissions',
        help="Commissions to reimburse to employee.",
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    commission_count = fields.Integer(compute='_compute_commission_count')

    @api.depends('commission_payment_ids.commission_ids', 'commission_payment_ids.payslip_id')
    def _compute_commission_count(self):
        for payslip in self:
            payslip.commission_count = len(payslip.mapped('commission_payment_ids.commission_ids'))

    @api.model_create_multi
    def create(self, vals_list):
        payslips = super().create(vals_list)
        draft_slips = payslips.filtered(lambda p: p.employee_id and p.state == 'draft')
        if not draft_slips:
            return payslips
        
        commission_payments = self.env['hr.commission.payment'].search([
            ('employee_id', 'in', draft_slips.mapped('employee_id').ids),
            ('pay_in_payslip', '=', True),
            ('payslip_id', '=', False)])
        for slip in draft_slips:
            payslip_commission_payments = commission_payments.filtered(lambda c: c.employee_id == slip.employee_id)
            slip.commission_payment_ids = [(5, 0, 0)] + [(4, c.id, False) for c in payslip_commission_payments]
        return payslips

    def write(self, vals):
        res = super().write(vals)
        if 'commission_payment_ids' in vals:
            self._compute_commission_input_line_ids()
        if 'input_line_ids' in vals:
            self._update_commission()
        return res
    
    def _update_commission(self):
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        for payslip in self:
            if not payslip.input_line_ids.filtered(lambda line: line.input_type_id == commission_type):
                payslip.commission_payment_ids.write({'payslip_id': False})

    def _compute_commission_input_line_ids(self):
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        if not commission_type:
            return
        for payslip in self:
            amount = sum(self.commission_payment_ids.mapped('commission_amount'))
            if not amount:
                continue
            lines_to_remove = payslip.input_line_ids.filtered(lambda x: x.input_type_id == commission_type)
            input_lines_vals = [(2, line.id, False) for line in lines_to_remove]
            input_lines_vals.append((0, 0, {
                'amount': amount,
                'input_type_id': commission_type.id
            }))
            payslip.update({'input_line_ids': input_lines_vals})

    def open_commissions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reimbursed Commissions'),
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('commission_payment_ids.commission_ids').ids)],
        }
