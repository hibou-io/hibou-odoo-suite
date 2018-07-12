from odoo import api, fields, models


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_payslip_done(self):
        res = super(HRPayslip, self).action_payslip_done()
        if res and isinstance(res, (int, bool)):
            holidays = self.env['hr.holidays'].sudo()
            leaves_to_update = holidays.search([('employee_id', '=', self.employee_id.id),
                                               ('accrue_by_pay_period', '=', True)])
            for leave_to_update in leaves_to_update:
                new_allocation = leave_to_update.number_of_days_temp + leave_to_update.allocation_per_period
                leave_to_update.write({'number_of_days_temp': new_allocation})

        return res


class HRHolidays(models.Model):
    _inherit = 'hr.holidays'

    accrue_by_pay_period = fields.Boolean(string="Accrue by Pay Period")
    allocation_per_period = fields.Float(string="Allocation Per Pay Period", digits=(12, 4))

    def _accrue_for_employee_values(self, employee):
        values = super(HRHolidays, self)._accrue_for_employee_values(employee)
        if values:
            values['accrue_by_pay_period'] = self.accrue_by_pay_period
            values['allocation_per_period'] = self.allocation_per_period
        return values
