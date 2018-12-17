from odoo import api, fields, models
from math import ceil
from odoo.addons.hr_holidays.models.hr_holidays import HOURS_PER_DAY


class HRHoliday(models.Model):
    _inherit = 'hr.holidays'

    days_in_hours = fields.Float(string="Hours", compute='_get_days_in_hours')

    def _get_number_of_days(self, date_from, date_to, employee_id):
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            num_days = employee.get_work_days_count(from_dt, to_dt)
            if num_days == 0:
                time_delta = to_dt - from_dt
                hours = (time_delta.seconds / 3600)
                return hours / HOURS_PER_DAY
            else:
                return employee.get_work_days_count(from_dt, to_dt)

        time_delta = to_dt - from_dt
        return ceil(time_delta.days + float(time_delta.seconds) / 86400)

    @api.depends('number_of_days_temp')
    def _get_days_in_hours(self):
        self.days_in_hours = self.number_of_days_temp * 8
