from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_state = fields.Selection(selection_add=[('break', 'Break'), ('lunch', 'Lunch')])

    @api.depends('last_attendance_id.work_type_id', 'last_attendance_id.check_in', 'last_attendance_id.check_out', 'last_attendance_id')
    def _compute_attendance_state(self):
        for employee in self:
            att = employee.last_attendance_id.sudo()
            if not att or att.check_out:
                employee.attendance_state = 'checked_out'
            elif employee.last_attendance_id.work_type_id.attendance_state:
                employee.attendance_state = employee.last_attendance_id.work_type_id.attendance_state
            else:
                employee.attendance_state = 'checked_in'

    def attendance_manual(self, next_action, entered_pin=None, work_type_id=None):
        self = self.with_context(work_type_id=work_type_id)
        if not entered_pin:
            # fix for pin mode with specific argument order for work_type_id
            entered_pin = None
        return super(HrEmployee, self).attendance_manual(next_action, entered_pin=entered_pin)

    def _attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()
        work_type_id = self._context.get('work_type_id', False)

        if self.attendance_state == 'checked_out':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            if work_type_id:
                # if we don't have a work_type_id, we want the default
                vals['work_type_id'] = work_type_id
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance and work_type_id:
            # work_type_id is the "next" attendance type
            attendance.check_out = action_date
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'work_type_id': work_type_id,
            }
            return self.env['hr.attendance'].create(vals)
        if attendance:
            attendance.check_out = action_date
        else:
            raise UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance
