# -*- coding: utf-8 -*-
from odoo import api, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        def create_empty_worked_lines(employee_id, contract_id, date_from, date_to):
            attendance = {
                'name': 'Timesheet Attendance',
                'sequence': 10,
                'code': 'ATTN',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract_id,
            }

            valid_days = [
                ('sheet_id.employee_id', '=', employee_id),
                ('sheet_id.state', '=', 'done'),
                ('sheet_id.date_from', '>=', date_from),
                ('sheet_id.date_to', '<=', date_to),
            ]
            return attendance, valid_days

        attendances = []

        for contract in contracts:
            attendance, valid_days = create_empty_worked_lines(
                contract.employee_id.id,
                contract.id,
                date_from,
                date_to
            )

            for day in self.env['hr_timesheet_sheet.sheet.day'].search(valid_days):
                if day.total_attendance >= 0.0:
                    attendance['number_of_days'] += 1
                    attendance['number_of_hours'] += day.total_attendance

            # needed so that the shown hours matches any calculations you use them for
            attendance['number_of_hours'] = round(attendance['number_of_hours'], 2)
            attendances.append(attendance)

        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        res.extend(attendances)
        return res

