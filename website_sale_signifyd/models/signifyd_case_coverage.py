from odoo import fields, models


class SignifydCaseCoverage(models.Model):
    _name = 'signifyd.case.coverage'

    case_id = fields.Many2one('signifyd.case', required=True)
    coverage_type_id = fields.Many2one('signifyd.coverage', required=True)
    amount = fields.Float()
    currency_id = fields.Many2one('res.currency')
