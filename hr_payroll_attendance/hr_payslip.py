from collections import defaultdict
from odoo import api, models
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        def create_empty_worked_lines(employee, contract, date_from, date_to):
            attn = {
                'name': 'Attendance',
                'sequence': 10,
                'code': 'ATTN',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }

            valid_attn = [
                ('employee_id', '=', employee.id),
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to),
            ]
            return attn, valid_attn

        work = []
        for contract in contracts.filtered(lambda c: c.paid_hourly_attendance):
            worked_attn, valid_attn = create_empty_worked_lines(
                contract.employee_id,
                contract,
                date_from,
                date_to
            )
            days = set()
            for attn in self.env['hr.attendance'].search(valid_attn):
                if not attn.check_out:
                    raise ValidationError('This pay period must not have any open attendances.')
                if attn.worked_hours:
                    # Avoid in/outs
                    attn_iso = attn.check_in.isocalendar()
                    if not attn_iso in days:
                        worked_attn['number_of_days'] += 1
                        days.add(attn_iso)
                    worked_attn['number_of_hours'] += attn.worked_hours
            worked_attn['number_of_hours'] = round(worked_attn['number_of_hours'], 2)
            work.append(worked_attn)

        res = super(HrPayslip, self).get_worked_day_lines(contracts.filtered(lambda c: not c.paid_hourly_attendance), date_from, date_to)
        res.extend(work)
        return res

    @api.multi
    def hour_break_down(self, code):
        """
        :param code: what kind of worked days you need aggregated
        :return: dict: keys are isocalendar tuples, values are hours.
        """
        self.ensure_one()
        if code == 'ATTN':
            attns = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', self.date_to),
            ])
            day_values = defaultdict(float)
            for attn in attns:
                if not attn.check_out:
                    raise ValidationError('This pay period must not have any open attendances.')
                if attn.worked_hours:
                    # Avoid in/outs
                    attn_iso = attn.check_in.isocalendar()
                    day_values[attn_iso] += attn.worked_hours
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
