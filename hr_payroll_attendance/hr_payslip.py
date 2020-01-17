from collections import defaultdict
from odoo import api, models
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        work = []
        for contract in contracts.filtered(lambda c: c.paid_hourly_attendance):
            attendance_line_data = self._attendance_create_lines(contract.employee_id, contract, date_from, date_to)
            attendance_breakdown = self._attendance_hour_break_down(contract.employee_id, contract, date_from, date_to)
            self._attendance_fill_lines(attendance_line_data, attendance_breakdown)
            for code, attn in attendance_line_data.items():
                work.append(attn)
        res = super(HrPayslip, self).get_worked_day_lines(contracts.filtered(lambda c: not c.paid_hourly_attendance), date_from, date_to)
        res.extend(work)
        return res

    def _attendance_fill_lines(self, lines, attendance_break_down):
        # Override to change comutation (e.g. grouping by week for overtime)
        # probably want to override _attendance_create_lines
        for isoday, worked_hours in attendance_break_down.items():
            lines['ATTN']['number_of_days'] += 1
            lines['ATTN']['number_of_hours'] += worked_hours

    def _attendance_create_lines(self, employee, contract, date_from, date_to):
        # Override to return more keys like this (e.g. OT Overtime)
        return {
            'ATTN': {
                'name': 'Attendance',
                'sequence': 10,
                'code': 'ATTN',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
        }

    def _attendance_domain(self, employee, contract, date_from, date_to):
        # Override if you need to limit by contract or similar.
        return [
            ('employee_id', '=', employee.id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to),
        ]

    def _attendance_get(self, employee, contract, date_from, date_to):
        # Override if you need to limit by contract or similar.
        return self.env['hr.attendance'].search(self._attendance_domain(employee, contract, date_from, date_to))

    def _attendance_hour_break_down(self, employee, contract, date_from, date_to):
        attns = self._attendance_get(employee, contract, date_from, date_to)
        day_values = defaultdict(float)
        for attn in attns:
            if not attn.check_out:
                raise ValidationError('This pay period must not have any open attendances.')
            if attn.worked_hours:
                # Avoid in/outs
                attn_iso = attn.check_in.isocalendar()
                day_values[attn_iso] += attn.worked_hours
        return day_values

    @api.multi
    def hour_break_down(self, code):
        """
        :param code: what kind of worked days you need aggregated
        :return: dict: keys are isocalendar tuples, values are hours.
        """
        self.ensure_one()
        if code == 'ATTN':
            return self._attendance_hour_break_down(self.employee_id, self.contract_id, self.date_from, self.date_to)
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
