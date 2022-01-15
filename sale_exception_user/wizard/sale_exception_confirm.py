# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class SaleExceptionConfirm(models.TransientModel):
    _inherit = 'sale.exception.confirm'

    def action_confirm(self):
        res = super().action_confirm()
        if self.ignore:
            self.related_model_id.action_confirm()
        return res

    def _action_ignore(self):
        self.related_model_id.ignore_exception = True
        self.related_model_id.action_confirm()
        return super()._action_ignore()
