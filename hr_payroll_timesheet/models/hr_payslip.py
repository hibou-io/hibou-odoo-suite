# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    timesheet_ids = fields.One2many('account.analytic.line', 'payslip_id', string='Timesheets',
                                     help='Timesheets represented by payslip.', readonly=True,
                                     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    timesheet_count = fields.Integer(compute='_compute_timesheet_count')

    @api.depends('timesheet_ids', 'timesheet_ids.payslip_id')
    def _compute_timesheet_count(self):
        for payslip in self:
            payslip.timesheet_count = len(payslip.timesheet_ids)

    def _filter_worked_day_lines_values(self, worked_day_lines_values):
        worked_day_lines_values = super()._filter_worked_day_lines_values(worked_day_lines_values)
        if self.contract_id.paid_hourly_timesheet:
            original_work_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
            if original_work_type:
                # filter out "work calendar lines"
                return [w for w in worked_day_lines_values if w['work_entry_type_id'] != original_work_type.id]
        return worked_day_lines_values

    def _pre_aggregate_work_data(self):
        work_data = super()._pre_aggregate_work_data()
        if self.contract_id.paid_hourly_timesheet:
            timesheet_to_keep = self.timesheet_ids.filtered(lambda ts: ts.employee_id == self.employee_id
                                                                       and ts.date <= self.date_to)
            timesheet_to_keep |= self.env['account.analytic.line'].search([
                ('employee_id', '=', self.employee_id.id),
                ('date', '<=', self.date_to),
                ('payslip_id', '=', False),
            ])
            self.update({'timesheet_ids': [(6, 0, timesheet_to_keep.ids)]})

            timesheet_type = self.env.ref('hr_timesheet_work_entry.work_input_timesheet', raise_if_not_found=False)
            if not timesheet_type:
                # different default type
                timesheet_type = self.struct_id.type_id.default_work_entry_type_id
                if not timesheet_type:
                    # return early, include the "work calendar lines"
                    return work_data
            work_data = self._pre_aggregate_timesheet_data(work_data, timesheet_type)
        return work_data

    def _pre_aggregate_timesheet_data(self, work_data, default_workentrytype):
        for ts in self.timesheet_ids.sorted('create_date'):
            if ts.unit_amount:
                ts_iso = ts.date.isocalendar()
                timesheet_type = ts.work_type_id or default_workentrytype
                if timesheet_type in self.struct_id.unpaid_work_entry_type_ids:
                    # this is unpaid, so we have to skip it from aggregation
                    continue
                work_data[ts_iso].append((timesheet_type, ts.unit_amount, ts))
        return work_data

    def action_open_timesheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Timesheets'),
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_payslip_id': self.id,
            },
            'domain': [('id', 'in', self.timesheet_ids.ids)],
        }
