# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class InvoiceExceptionConfirm(models.TransientModel):
    _name = 'invoice.exception.confirm'
    _inherit = ['exception.rule.confirm']
    _description = 'Invoice Exception Confirm Wizard'

    related_model_id = fields.Many2one('account.move', 'Invoice')

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        res = super().action_confirm()
        if self.ignore:
            return self.related_model_id.action_post()
        else:
            return res

    def _action_ignore(self):
        self.related_model_id.ignore_exception = True
        super()._action_ignore()
        return self.related_model_id.action_post()
