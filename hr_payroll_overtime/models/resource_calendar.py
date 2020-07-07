from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    day_week_start = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday'),
    ], string='Day Week Starts', required=True, default='1')
