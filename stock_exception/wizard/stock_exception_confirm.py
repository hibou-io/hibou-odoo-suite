# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class StockExceptionConfirm(models.TransientModel):
    _name = 'stock.exception.confirm'
    _inherit = ['exception.rule.confirm']
    _description = 'Stock Exception Confirm Wizard'

    related_model_id = fields.Many2one('stock.picking', 'Transfer')

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        res = super().action_confirm()
        if self.ignore:
            return self.related_model_id.button_validate()
        else:
            return res

    def _action_ignore(self):
        self.related_model_id.ignore_exception = True
        super()._action_ignore()
        return self.related_model_id.button_validate()
