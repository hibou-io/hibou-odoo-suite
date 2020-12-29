from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_remaining = fields.Float('Credit Remaining', compute='_compute_credit_remaining')
    credit_hold = fields.Boolean('Credit Hold')

    @api.depends('credit_limit', 'credit')
    def _compute_credit_remaining(self):
        for partner in self:
            if partner.credit_limit:
                partner.credit_remaining = partner.credit_limit - partner.credit
            else:
                partner.credit_remaining = 0.0
