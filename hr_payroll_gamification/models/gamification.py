from odoo import api, fields, models


class GamificationBadge(models.Model):
    _inherit = 'gamification.badge'

    payroll_type = fields.Selection([
        ('', 'None'),
        ('fixed', 'Fixed'),
    ], string='Payroll Type')
    payroll_amount = fields.Float(string='Payroll Amount', digits=(10, 4))
