# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_ids = fields.One2many('hr.attendance', 'payslip_id', string='Attendances',
                                     help='Attendances represented by payslip.', readonly=True,
                                     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    attendance_count = fields.Integer(compute='_compute_attendance_count')

    @api.depends('attendance_ids', 'attendance_ids.payslip_id')
    def _compute_attendance_count(self):
        for payslip in self:
            payslip.attendance_count = len(payslip.attendance_ids)

    def _filter_worked_day_lines_values(self, worked_day_lines_values):
        worked_day_lines_values = super()._filter_worked_day_lines_values(worked_day_lines_values)
        if self.contract_id.paid_hourly_attendance:
            original_work_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
            if original_work_type:
                # filter out "work calendar lines"
                return [w for w in worked_day_lines_values if w['work_entry_type_id'] != original_work_type.id]
        return worked_day_lines_values

    def _pre_aggregate_work_data(self):
        work_data = super()._pre_aggregate_work_data()
        if self.contract_id.paid_hourly_attendance:
            attendance_to_keep = self.attendance_ids.filtered(lambda a: a.employee_id == self.employee_id
                                                                        and a.check_out.date() <= self.date_to)
            attendance_to_keep |= self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_out', '<=', self.date_to),
                ('payslip_id', '=', False),
            ])
            self.update({'attendance_ids': [(6, 0, attendance_to_keep.ids)]})

            attendance_type = self.env.ref('hr_attendance_work_entry.work_input_attendance', raise_if_not_found=False)
            if not attendance_type:
                # different default type
                attendance_type = self.struct_id.type_id.default_work_entry_type_id
                if not attendance_type:
                    # return early, include the "work calendar lines"
                    return work_data
            work_data = self._pre_aggregate_attendance_data(work_data, attendance_type)
        return work_data

    def _pre_aggregate_attendance_data(self, work_data, default_workentrytype):
        for attn in self.attendance_ids:
            if attn.worked_hours:
                # Avoid in/outs
                attn_iso = attn.check_in.isocalendar()
                attendance_type = attn.work_type_id or default_workentrytype
                if attendance_type in self.struct_id.unpaid_work_entry_type_ids:
                    # this is unpaid, so we have to skip it from aggregation
                    # if we don't then they will be eligible for overtime even
                    # if this time wasn't intended to be paid
                    continue
                work_data[attn_iso].append((attendance_type, attn.worked_hours, attn))
        return work_data

    def action_open_attendances(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Attendances'),
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_payslip_id': self.id,
            },
            'domain': [('id', 'in', self.attendance_ids.ids)],
        }
