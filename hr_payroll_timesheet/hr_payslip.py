# -*- coding: utf-8 -*-
from openerp import models, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        def create_empty_timesheet_worked_lines(employee_id, contract_id, date_from, date_to):
            timesheet = {
                'name': 'Timesheet Entries',
                'sequence': 20,
                'code': 'TS',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract_id,
            }

            valid_sheets = [
                ('employee_id', '=', employee_id),
                ('state', '=', 'done'),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ]
            return timesheet, valid_sheets

        def create_empty_attendance_worked_lines(employee_id, contract_id, date_from, date_to):
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

        worked_lines = []

        for contract in self.env['hr.contract'].browse(contract_ids):
            timesheet, valid_sheets = create_empty_timesheet_worked_lines(
                contract.employee_id.id,
                contract.id,
                date_from,
                date_to
            )
            days = set()
            hours = 0.0
            sheets = self.sudo().env['hr_timesheet_sheet.sheet'].search(valid_sheets)
            # Don't use .mapped('timesheet_ids') as that will not work.
            entries = self.env['account.analytic.line'].search([('sheet_id', 'in', sheets.ids)])
            for line in entries:
                days.add(line.date)
                hours += line.unit_amount
            if days:
                timesheet['number_of_days'] = len(days)
                timesheet['number_of_hours'] = hours
                worked_lines.append(timesheet)

            attendance_model = getattr(self.env, 'hr_timesheet_sheet.sheet.day', None)
            if attendance_model:
                attendance, valid_days = create_empty_attendance_worked_lines(
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
                worked_lines.append(attendance)

        return super(HrPayslip, self).get_worked_day_lines(contract_ids, date_from, date_to) + worked_lines

