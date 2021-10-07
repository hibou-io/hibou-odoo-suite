# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    commission_structure_id = fields.Many2one('hr.commission.structure', string='Commission Structure')
