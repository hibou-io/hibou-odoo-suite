# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from collections import defaultdict
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

    def _get_worked_day_lines(self):
        # Called at the end of _onchange_employee()
        worked_day_lines = super()._get_worked_day_lines()
        return self._attendance_get_worked_day_lines(worked_day_lines)

    def _attendance_get_worked_day_lines(self, worked_day_lines):
        """
        Filters out basic "Attendance"/"Work Calendar" entries as they would add to salary.
        Note that this is during an onchange (probably).
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        if not self.contract_id.paid_hourly_attendance:
            return worked_day_lines
        if not self.state in ('draft', 'verify'):
            return worked_day_lines

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
                return worked_day_lines

        original_work_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        if original_work_type:
            # filter out "work calendar lines"
            worked_day_lines = [w for w in worked_day_lines if w['work_entry_type_id'] != original_work_type.id]

        # normalize leaves
        self._attendance_normalize_other_work_lines(worked_day_lines)

        work_data = self._pre_aggregate_attendance_data(attendance_type)
        processed_data = self.aggregate_overtime(work_data)

        worked_day_lines += [{
                'number_of_days': data[0],
                'number_of_hours': data[1],
                'amount': data[1] * data[2] * self._wage_for_work_type(work_type),
                'contract_id': self.contract_id.id,
                'work_entry_type_id': work_type.id,
            } for work_type, data in processed_data.items()]

        return worked_day_lines

    def _attendance_normalize_other_work_lines(self, worked_day_line_values):
        # Modifies the values based on 'wage'
        unpaid_work_entry_types = self.struct_id.unpaid_work_entry_type_ids
        for line_vals in worked_day_line_values:
            work_type = self.env['hr.work.entry.type'].browse(line_vals['work_entry_type_id'])
            if work_type not in unpaid_work_entry_types:
                line_vals['amount'] = line_vals.get('number_of_hours', 0.0) * self._wage_for_work_type(work_type)
            else:
                line_vals['amount'] = 0.0

    def _wage_for_work_type(self, work_type):
        # Override if you pay differently for different work types
        return self.contract_id.wage

    def _pre_aggregate_attendance_data(self, default_workentrytype):
        worked_attn = defaultdict(list)
        for attn in self.attendance_ids:
            if attn.worked_hours:
                # Avoid in/outs
                attn_iso = attn.check_in.isocalendar()
                attendance_type = attn.work_type_id or default_workentrytype
                if attendance_type in self.struct_id.unpaid_work_entry_type_ids:
                    # this is unpaid, so we have to skip it from aggregation
                    continue
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
