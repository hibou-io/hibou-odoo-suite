# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    commission_rate = fields.Float(string='Commission %', default=0.0)
    admin_commission_rate = fields.Float(string='Admin Commission %', default=0.0)

