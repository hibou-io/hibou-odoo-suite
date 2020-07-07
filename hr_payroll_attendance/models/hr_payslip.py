from collections import defaultdict
from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_ids = fields.One2many('hr.attendance', 'payslip_id', string='Attendances',
                                     help='Attendances represented by payslip.',
                                     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    attendance_count = fields.Integer(compute='_compute_attendance_count')

    @api.depends('attendance_ids', 'attendance_ids.payslip_id')
    def _compute_attendance_count(self):
        for payslip in self:
            payslip.attendance_count = len(payslip.attendance_ids)

    @api.onchange('worked_days_line_ids')
    def _onchange_worked_days_line_ids(self):
        # super()._onchange_worked_days_line_ids()
        attendance_type = self.env.ref('hr_payroll_attendance.work_input_attendance', raise_if_not_found=False)
        if not self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id == attendance_type):
            self.attendance_ids.write({'payslip_id': False})

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super()._onchange_employee()
        if self.state == 'draft' and self.contract_id.paid_hourly_attendance:
            self.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_out', '<=', self.date_to),
                '|', ('payslip_id', '=', False),
                     ('payslip_id', '=', self.id),
            ])
            self._onchange_attendance_ids()
        return res

    @api.onchange('attendance_ids')
    def _onchange_attendance_ids(self):
        original_work_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        attendance_type = self.env.ref('hr_payroll_attendance.work_input_attendance', raise_if_not_found=False)
        if not attendance_type:
            return

        if original_work_type:
            types_to_remove = original_work_type + attendance_type
        else:
            types_to_remove = attendance_type

        work_data = self._pre_aggregate_attendance_data()
        processed_data = self.aggregate_overtime(work_data)

        lines_to_keep = self.worked_days_line_ids.filtered(lambda x: x.work_entry_type_id not in types_to_remove)
        # Note that [(5, 0, 0)] + [(4, 999, 0)], will not work
        work_lines_vals = [(3, line.id, False) for line in (self.worked_days_line_ids - lines_to_keep)]
        work_lines_vals += [(4, line.id, False) for line in lines_to_keep]
        work_lines_vals += [(0, 0, {
            'number_of_days': data[0],
            'number_of_hours': data[1],
            'amount': data[1] * data[2] * self._wage_for_work_type(work_type),
            'contract_id': self.contract_id.id,
            'work_entry_type_id': work_type.id,
        }) for work_type, data in processed_data.items()]
        self.update({'worked_days_line_ids': work_lines_vals})

    def _wage_for_work_type(self, work_type):
        # Override if you pay differently for different work types
        return self.contract_id.wage

    def _pre_aggregate_attendance_data(self):
        attendance_type = self.env.ref('hr_payroll_attendance.work_input_attendance', raise_if_not_found=False)
        worked_attn = defaultdict(list)
        for attn in self.attendance_ids:
            if attn.worked_hours:
                # Avoid in/outs
                attn_iso = attn.check_in.isocalendar()
                worked_attn[attn_iso].append((attendance_type, attn.worked_hours, attn))
        res = [(k, worked_attn[k]) for k in sorted(worked_attn.keys())]
        return res

    def action_open_attendances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Attendances'),
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.attendance_ids.ids)],
        }
