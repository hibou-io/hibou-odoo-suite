# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _


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

    @api.onchange('input_line_ids')
    def _onchange_input_line_ids(self):
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        if not self.input_line_ids.filtered(lambda line: line.input_type_id == commission_type):
            self.commission_payment_ids.write({'payslip_id': False})

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super()._onchange_employee()
        if self.state == 'draft':
            self.commission_payment_ids = self.env['hr.commission.payment'].search([
                ('employee_id', '=', self.employee_id.id),
                ('pay_in_payslip', '=', True),
                ('payslip_id', '=', False)])
            self._onchange_commission_payment_ids()
        return res

    @api.onchange('commission_payment_ids')
    def _onchange_commission_payment_ids(self):
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        if not commission_type:
            return

        total = sum(self.commission_payment_ids.mapped('commission_amount'))
        if not total:
            return

        lines_to_keep = self.input_line_ids.filtered(lambda x: x.input_type_id != commission_type)
        input_lines_vals = [(5, 0, 0)] + [(4, line.id, False) for line in lines_to_keep]
        input_lines_vals.append((0, 0, {
            'amount': total,
            'input_type_id': commission_type.id,
        }))
        self.update({'input_line_ids': input_lines_vals})

    def open_commissions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reimbursed Commissions'),
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('commission_payment_ids.commission_ids').ids)],
        }
