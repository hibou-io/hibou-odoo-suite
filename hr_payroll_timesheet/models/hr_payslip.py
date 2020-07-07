from collections import defaultdict
from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    timesheet_ids = fields.One2many('account.analytic.line', 'payslip_id', string='Timesheets',
                                     help='Timesheets represented by payslip.',
                                     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    timesheet_count = fields.Integer(compute='_compute_timesheet_count')

    @api.depends('timesheet_ids', 'timesheet_ids.payslip_id')
    def _compute_timesheet_count(self):
        for payslip in self:
            payslip.timesheet_count = len(payslip.timesheet_ids)

    @api.onchange('worked_days_line_ids')
    def _onchange_worked_days_line_ids(self):
        # super()._onchange_worked_days_line_ids()
        timesheet_type = self.env.ref('hr_payroll_timesheet.work_input_timesheet', raise_if_not_found=False)
        if not self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id == timesheet_type):
            self.timesheet_ids.write({'payslip_id': False})

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super()._onchange_employee()
        if self.state == 'draft' and self.contract_id.paid_hourly_timesheet:
            self.timesheet_ids = self.env['account.analytic.line'].search([
                ('employee_id', '=', self.employee_id.id),
                ('date', '<=', self.date_to),
                '|', ('payslip_id', '=', False),
                     ('payslip_id', '=', self.id),
            ])
            self._onchange_timesheet_ids()
        return res

    @api.onchange('timesheet_ids')
    def _onchange_timesheet_ids(self):
        timesheet_type = self.env.ref('hr_payroll_timesheet.work_input_timesheet', raise_if_not_found=False)
        if not timesheet_type:
            return

        original_work_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        if original_work_type:
            types_to_remove = original_work_type + timesheet_type
        else:
            types_to_remove = timesheet_type

        work_data = self._pre_aggregate_timesheet_data()
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

    def _pre_aggregate_timesheet_data(self):
        timesheet_type = self.env.ref('hr_payroll_timesheet.work_input_timesheet', raise_if_not_found=False)
        worked_ts = defaultdict(list)
        for ts in self.timesheet_ids.sorted('id'):
            if ts.unit_amount:
                ts_iso = ts.date.isocalendar()
                worked_ts[ts_iso].append((timesheet_type, ts.unit_amount, ts))
        res = [(k, worked_ts[k]) for k in sorted(worked_ts.keys())]
        return res

    def action_open_timesheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Timesheets'),
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.timesheet_ids.ids)],
        }
