from odoo import fields, models


class SignifydCoverage(models.Model):
    _name = 'signifyd.coverage'
    _description = 'Signifyd Coverage type'

    name = fields.Char(required=True)
    description = fields.Char()
    code = fields.Char(required=True)
    exclusive = fields.Boolean())

    def _apply_exclusivity(self):
        return self.filtered('exclusive')[:1] or self
