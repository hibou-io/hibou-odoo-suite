from math import floor
from odoo import api, fields, models


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    usage_uom_id = fields.Many2one('uom.uom', string='Usage UOM')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    employee_id = fields.Many2one(track_visibility=False)
    department_id = fields.Many2one(track_visibility=False)
    usage_qty = fields.Float(string='Usage', default=0.0)
    usage_uom_id = fields.Many2one('uom.uom', related='category_id.usage_uom_id')
    usage_log_ids = fields.One2many('maintenance.usage.log', 'equipment_id', string='Usage')
    usage_count = fields.Integer(string='Usage Count', compute='_compute_usage_count')
    maintenance_usage = fields.Float(string='Preventative Usage')

    def _compute_usage_count(self):
        for equipment in self:
            equipment.usage_count = len(equipment.usage_log_ids)

    @api.model
    def create(self, values):
        record = super(MaintenanceEquipment, self).create(values)
        # create first usage record
        record._log_usage()
        return record

    def write(self, values):
        usage_qty = values.get('usage_qty')
        employee_id = values.get('employee_id')
        department_id = values.get('department_id')
        if any((usage_qty, employee_id, department_id)):
            for equipment in self:
                log_values = {}

                if (equipment.usage_qty is not None
                        and usage_qty is not None
                        and abs(usage_qty - equipment.usage_qty) > 0.0001):
                    log_values['qty'] = usage_qty
                if employee_id != equipment.employee_id.id:
                    log_values['employee_id'] = employee_id
                if department_id != equipment.department_id.id:
                    log_values['department_id'] = department_id

                if log_values:
                    equipment._log_usage(values=log_values)

        # Check to have the original fields before write.
        self._check_maintenance_usage(usage_qty)

        result = super(MaintenanceEquipment, self).write(values)
        return result

    def _log_usage(self, values=None):
        if not values:
            values = {}
        values['equipment_id'] = self.id
        values['date'] = fields.Datetime.now()
        self.env['maintenance.usage.log'].create(values)

    def _check_maintenance_usage(self, usage_qty):
        for e in self.filtered(lambda e: e.maintenance_usage):
            try:
                if floor(e.usage_qty / e.maintenance_usage) != floor(usage_qty / e.maintenance_usage):
                    next_requests = self.env['maintenance.request'].search([('stage_id.done', '=', False),
                                                                            ('equipment_id', '=', e.id),
                                                                            ('maintenance_type', '=', 'preventive'),
                                                                           ])
                    if not next_requests:
                        e._create_new_request(fields.Date.today())
            except TypeError:
                pass

    def action_open_usage_log(self):
        for equipment in self:
            action = self.env.ref('maintenance_usage.maintenance_usage_log_action_reports').read()[0]
            action['domain'] = [('equipment_id', '=', equipment.id)]
            action['context'] = {
                    'default_equipment_id': equipment.id,
                    'default_employee_id': equipment.employee_id.id,
                    'default_department_id': equipment.department_id.id,
                    'default_qty': equipment.usage_qty,
                }
            return action


class MaintenanceUsageLog(models.Model):
    _name = 'maintenance.usage.log'
    _order = 'date DESC'
    _log_access = False

    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one(string='Unit of Measure', related='equipment_id.category_id.usage_uom_id')

    @api.model
    def create(self, values):
        equipment = self.env['maintenance.equipment'].browse(values.get('equipment_id'))
        if not values.get('employee_id'):
            values['employee_id'] = equipment.employee_id.id
        if not values.get('department_id'):
            values['department_id'] = equipment.department_id.id
        if not values.get('qty'):
            values['qty'] = equipment.usage_qty
        return super(MaintenanceUsageLog, self).create(values)
