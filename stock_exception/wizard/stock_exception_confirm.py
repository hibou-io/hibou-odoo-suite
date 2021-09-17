from odoo import api, fields, models


class StockExceptionConfirm(models.TransientModel):
    _name = 'stock.exception.confirm'
    _inherit = ['exception.rule.confirm']

    related_model_id = fields.Many2one('stock.picking', 'Transfer')

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        return super().action_confirm()