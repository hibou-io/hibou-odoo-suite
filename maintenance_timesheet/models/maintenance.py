from odoo import api, fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    maintenance_request_id = fields.Many2one('maintenance.request')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    def action_open_maintenance_requests(self):
        self.ensure_one()
        action = self.env.ref('maintenance.hr_equipment_request_action_from_equipment').read()[0]
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_employee_id': self.employee_id.id,
            'default_department_id': self.department_id.id,
        }
        return action


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    project_id = fields.Many2one('project.project', string='Billing Project')
    timesheet_ids = fields.One2many('account.analytic.line', 'maintenance_request_id', 'Timesheets')
    effective_hours = fields.Float(compute='_hours_get', store=True, string='Hours Spent',
                                   help="Computed using the sum of the maintenance work done.")
    remaining_hours = fields.Float(compute='_hours_get', store=True, string='Remaining Hours',
                                   help="Total remaining time.")

    @api.model
    def create(self, values):
        if not values.get('project_id') and values.get('department_id'):
            department = self.env['hr.department'].browse(values.get('department_id'))
            if department and department.project_ids:
                values.update({'project_id': department.project_ids.ids[0]})
        return super(MaintenanceRequest, self).create(values)

    @api.depends('duration', 'timesheet_ids.unit_amount')
    def _hours_get(self):
        for request in self:
            effective_hours = sum(request.sudo().timesheet_ids.mapped('unit_amount'))
            request.effective_hours = effective_hours
            request.remaining_hours = (request.duration or 0.0) - effective_hours

    @api.onchange('department_id')
    def _onchange_department_id_project(self):
        for request in self:
            if request.department_id and request.department_id.project_ids:
                request.project_id = request.department_id.project_ids[0]
