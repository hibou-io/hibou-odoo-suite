from odoo import api, fields, models


class EquipmentChargeType(models.Model):
    _name = 'maintenance.equipment.charge.type'

    name = fields.Char(string='Charge Type')
    uom_id = fields.Many2one('uom.uom', string='Charge UOM')


class Equipment(models.Model):
    _inherit = 'maintenance.equipment'

    charge_ids = fields.One2many('maintenance.equipment.charge', 'equipment_id', 'Charges', copy=False)
    charge_count = fields.Integer(string='Charges', compute='_compute_charge_count')

    def _compute_charge_count(self):
        for equipment in self:
            self.charge_count = len(equipment.charge_ids)

    def action_open_charges(self):
        self.ensure_one()
        action = self.env.ref('maintenance_equipment_charge.maintenance_charge_action_reports').read()[0]
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_employee_id': self.employee_id.id,
            'default_department_id': self.department_id.id,
        }
        return action


class EquipmentCharge(models.Model):
    _name = 'maintenance.equipment.charge'
    _order = 'date DESC'

    name = fields.Char(string='Description')
    date = fields.Date(string='Date', default=fields.Date.today, index=True)
    equipment_id = fields.Many2one('maintenance.equipment', copy=False)
    type_id = fields.Many2one('maintenance.equipment.charge.type', string='Type')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    qty = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', related='type_id.uom_id')
    amount = fields.Float(string='Amount')
