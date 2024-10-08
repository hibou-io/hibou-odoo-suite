# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    # TODO: remove options no longer available in api v3
    signifyd_case_type = fields.Selection([
        ('', 'No Case'),
        ('SCORE', 'Score'),
        ('DECISION', 'Decision'),
        ('GUARANTEE', 'Guarantee'),
    ], string='Signifyd Case Creation', default='')
    signifyd_case_required = fields.Boolean(string='Create Signifyd Case', default=True)
    signifyd_coverage_ids = fields.Many2many('signifyd.coverage', string='Available Coverage Types',
        help='Note that exclusive coverage types will only allow one to be selected.')

    @api.onchange('signifyd_coverage_ids')
    def _onchange_signifyd_coverage_ids(self):
        self.signifyd_coverage_ids = self.signifyd_coverage_ids._apply_exclusivity()

    @api.onchange('signifyd_case_required')
    def _onchange_signifyd_case_required(self):
        if not self.signifyd_case_required:
            self.signifyd_coverage_ids = False