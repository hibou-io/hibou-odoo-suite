from odoo import models, fields, api


class USWAHrContract(models.Model):
    _inherit = 'hr.contract'

    wa_lni = fields.Many2one('hr.contract.lni.wa', string='WA State LNI')


class WALNI(models.Model):
    _name = 'hr.contract.lni.wa'

    name = fields.Char(string='Name')
    rate = fields.Float(string='Rate (per hour worked)', digits=(7, 6))
    rate_emp_withhold = fields.Float(string='Employee Payroll Deduction Rate (per hour worked)', digits=(7, 6))
