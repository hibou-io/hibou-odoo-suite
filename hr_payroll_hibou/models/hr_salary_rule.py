# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    schedule_pay = fields.Selection(selection_add=[
        ('semi-monthly', 'Semi-monthly'),
    ], ondelete={'semi-monthly': 'set null'})


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    default_schedule_pay = fields.Selection(selection_add=[
        ('semi-monthly', 'Semi-monthly'),
    ])
