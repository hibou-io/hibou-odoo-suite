from odoo import api, fields, models


class HRHolidays(models.Model):
    _inherit = 'hr.leave.type'

    grant_by_tag = fields.Boolean(string="Grant by Tag")

    def _accrue_for_employee_values(self, employee):
        return {
                'holiday_status_id': self.holiday_status_id.id,
                'number_of_days_temp': self.number_of_days_temp,
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'type': 'add',
                'state': 'confirm',
                'double_validation': self.double_validation,
                'grant_by_tag': self.grant_by_tag,
            }

    def accrue_for_employee(self, employee):
        holidays = self.env['hr.leave'].sudo()
        for leave_to_create in self:
            values = leave_to_create._accrue_for_employee_values(employee)
            if values:
                leave = holidays.create(values)
                leave.action_approve()


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.multi
    def write(self, values):
        holidays = self.env['hr.leave'].sudo()
        for emp in self:
            if values.get('category_ids'):
                categ_ids_command_list = values.get('category_ids')
                for categ_ids_command in categ_ids_command_list:
                    ids = None
                    if categ_ids_command[0] == 6:
                        ids = set(categ_ids_command[2])
                        ids -= set(emp.category_ids.ids)
                    if categ_ids_command[0] == 4:
                        id = categ_ids_command[1]
                        if id not in emp.category_ids.ids:
                            ids = [id]
                    if ids:
                        # new category ids
                        leaves = holidays.search([('category_id', 'in', list(ids)),
                                                  ('grant_by_tag', '=', True)])
                        leaves.accrue_for_employee(emp)

        return super(HREmployee, self).write(values)
