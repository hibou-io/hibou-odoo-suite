from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    purchase_date = fields.Date(string='Purchase Date')
    purchase_condition = fields.Selection([
                             ('new', 'New'),
                             ('used', 'Used'),
                             ('other', 'Other'),
                         ], string='Purchase Condition')
    purchase_note = fields.Text(string='Purchase Note')
