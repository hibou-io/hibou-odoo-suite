from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    valuation_in_account_id = fields.Many2one('account.account', company_dependent=True)
    valuation_out_account_id = fields.Many2one('account.account', company_dependent=True)
