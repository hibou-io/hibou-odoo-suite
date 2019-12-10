from collections import defaultdict
from odoo import models, api
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        leaves = {}

        for contract in contracts.filtered(lambda c: c.paid_hourly_timesheet):
            hours_per_day = contract.resource_calendar_id.hours_per_day or HOURS_PER_DAY
            for leave in self._fetch_valid_leaves_timesheet(contract.employee_id.id, date_from, date_to):
                leave_code = self._create_leave_code(leave.holiday_status_id.name)
                if leave_code in leaves:
                    leaves[leave_code]['number_of_days'] += leave.number_of_days
                    leaves[leave_code]['number_of_hours'] += leave.number_of_days * hours_per_day
                else:
                    leaves[leave_code] = {
                        'name': leave.holiday_status_id.name,
                        'sequence': 15,
                        'code': leave_code,
                        'number_of_days': leave.number_of_days,
                        'number_of_hours': leave.number_of_days * hours_per_day,
                        'contract_id': contract.id,
                    }

        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        res.extend(leaves.values())
        return res

    @api.multi
    def action_payslip_done(self):
        for slip in self.filtered(lambda s: s.contract_id.paid_hourly_timesheet):
            leaves = self._fetch_valid_leaves_timesheet(slip.employee_id.id, slip.date_from, slip.date_to)
            leaves.write({'payslip_status': True})
        return super(HrPayslip, self).action_payslip_done()

    def _fetch_valid_leaves_timesheet(self, employee_id, date_from, date_to):
        valid_leaves = [
            ('employee_id', '=', employee_id),
            ('state', '=', 'validate'),
            ('date_from', '>=', date_from),
            ('date_from', '<=', date_to),
            ('payslip_status', '=', False),
            ('holiday_status_id.unpaid', '=', False),
        ]

        return self.env['hr.leave'].search(valid_leaves)

    def _create_leave_code(self, name):
        return 'L_' + name.replace(' ', '_')


    @api.multi
    def hour_break_down(self, code):
        """
        :param code: what kind of worked days you need aggregated
        :return: dict: keys are isocalendar tuples, values are hours.
        """
        self.ensure_one()
        if code.startswith('L_'):
            hours_per_day = self.contract_id.resource_calendar_id.hours_per_day or HOURS_PER_DAY
            leaves = self._fetch_valid_leaves(self.employee_id.id, self.date_from, self.date_to)
            day_values = defaultdict(float)
            for leave in leaves:
                leave_code = self._create_leave_code(leave.holiday_status_id.name)
                if leave_code == code:
                    leave_iso = leave.date_from.isocalendar()
                    day_values[leave_iso] += leave.number_of_days * hours_per_day
            return day_values
        elif hasattr(super(HrPayslip, self), 'hour_break_down'):
            return super(HrPayslip, self).hour_break_down(code)
