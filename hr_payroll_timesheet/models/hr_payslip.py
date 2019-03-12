from collections import defaultdict
from odoo import api, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        work = []
        for contract in contracts.filtered(lambda c: c.paid_hourly_timesheet):
            # Only run on 'paid hourly timesheet' contracts.
            res = self._get_worked_day_lines_hourly_timesheet(contract, date_from, date_to)
            if res:
                work.append(res)

        res = super(HrPayslip, self).get_worked_day_lines(contracts.filtered(lambda c: not c.paid_hourly_timesheet), date_from, date_to)
        res.extend(work)
        return res

    def _get_worked_day_lines_hourly_timesheet(self, contract, date_from, date_to):
        """
        This would be a common hook to extend or break out more functionality, like pay rate based on project.
        Note that you will likely need to aggregate similarly in hour_break_down() and hour_break_down_week()
        :param contract: `hr.contract`
        :param date_from: str
        :param date_to: str
        :return: dict of values for `hr.payslip.worked_days`
        """
        values = {
            'name': 'Timesheet',
            'sequence': 15,
            'code': 'TS',
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
            'contract_id': contract.id,
        }

        valid_ts = [
            # ('is_timesheet', '=', True),
            # 'is_timesheet' is computed if there is a project_id associated with the entry
            ('project_id', '!=', False),
            ('employee_id', '=', contract.employee_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]

        days = set()
        for ts in self.env['account.analytic.line'].search(valid_ts):
            if ts.unit_amount:
                ts_iso = ts.date.isocalendar()
                if ts_iso not in days:
                    values['number_of_days'] += 1
                    days.add(ts_iso)
                values['number_of_hours'] += ts.unit_amount

        values['number_of_hours'] = round(values['number_of_hours'], 2)
        return values

    @api.multi
    def hour_break_down(self, code):
        """
        :param code: what kind of worked days you need aggregated
        :return: dict: keys are isocalendar tuples, values are hours.
        """
        self.ensure_one()
        if code == 'TS':
            timesheets = self.env['account.analytic.line'].search([
                # ('is_timesheet', '=', True),
                # 'is_timesheet' is computed if there is a project_id associated with the entry
                ('project_id', '!=', False),
                ('employee_id', '=', self.employee_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ])
            day_values = defaultdict(float)
            for ts in timesheets:
                if ts.unit_amount:
                    ts_iso = ts.date.isocalendar()
                    day_values[ts_iso] += ts.unit_amount
            return day_values
        elif hasattr(super(HrPayslip, self), 'hour_break_down'):
            return super(HrPayslip, self).hour_break_down(code)

    @api.multi
    def hours_break_down_week(self, code):
        """
        :param code: hat kind of worked days you need aggregated
        :return: dict: keys are isocalendar weeks, values are hours.
        """
        days = self.hour_break_down(code)
        weeks = defaultdict(float)
        for isoday, hours in days.items():
            weeks[isoday[1]] += hours
        return weeks
