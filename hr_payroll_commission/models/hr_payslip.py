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

    @api.onchange('input_line_ids')
    def _onchange_input_line_ids(self):
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        if not self.input_line_ids.filtered(lambda line: line.input_type_id == commission_type):
            self.commission_payment_ids.write({'payslip_id': False})

    def action_refresh_from_work_entries(self):
        res = super().action_refresh_from_work_entries()
        for slip in self.filtered(lambda s: s.state in ('draft', 'verify')):
            commission_payments = self.env['hr.commission.payment'].browse()
            if slip.employee_id:
                commission_payments = self.env['hr.commission.payment'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('pay_in_payslip', '=', True),
                    ('payslip_id', '=', False)])
            slip.commission_payment_ids = commission_payments
        return res

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to', 'struct_id', 'commission_payment_ids')
    def _compute_input_line_ids(self):
        res = super()._compute_input_line_ids()

        commission_type = self.env.ref('hr_payroll_commission.commission_other_input', raise_if_not_found=False)
        if not commission_type:
            return res

        for slip in self:
            amount = sum(self.commission_payment_ids.mapped('commission_amount'))
            if not amount:
                continue
            slip.update({
                'input_line_ids': [
                    Command.create({
                        'name': commission_type.name or 'Commission',
                        'amount': amount,
                        'input_type_id': commission_type.id,
                    }),
                ],
            })
        
        return res

    def open_commissions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reimbursed Commissions'),
            'res_model': 'hr.commission',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('commission_payment_ids.commission_ids').ids)],
        }
