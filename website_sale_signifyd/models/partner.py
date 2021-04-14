from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    signifyd_case_ids = fields.One2many('signifyd.case', 'partner_id', string='Signifyd Cases')
    signifyd_case_count = fields.Integer(compute='_compute_signifyd_stats', string='Signifyd Cases')
    signifyd_average_score = fields.Float(compute='_compute_signifyd_stats', string='Signifyd Score')

    def _compute_signifyd_stats(self):
        for record in self:
            cases = record.signifyd_case_ids
            if cases:
                record.signifyd_case_count = len(cases)
                record.signifyd_average_score = sum(cases.mapped('score')) / record.signifyd_case_count
            else:
                record.signifyd_case_count = 0
                record.signifyd_average_score = 0
