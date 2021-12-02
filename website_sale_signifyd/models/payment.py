# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    signifyd_case_type = fields.Selection([
        ('', 'No Case'),
        ('SCORE', 'Score'),
        ('DECISION', 'Decision'),
        ('GUARANTEE', 'Guarantee'),
    ], string='Signifyd Case Creation', default='')
