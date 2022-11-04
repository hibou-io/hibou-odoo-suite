# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    signifyd_case_type = fields.Selection([
        ('', 'No Case'),
        ('SCORE', 'Score'),
        ('DECISION', 'Decision'),
        ('GUARANTEE', 'Guarantee'),
    ], string='Signifyd Case Creation', default='')
