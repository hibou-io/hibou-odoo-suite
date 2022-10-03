# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class TimesheetExceptionConfirm(models.TransientModel):
    _name = 'timesheet.exception.confirm'
    _inherit = ['exception.rule.confirm']
    _description = 'Timesheet Exception Confirm Wizard'

    related_model_id = fields.Many2one('account.analytic.line', 'AnalyticLine')

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        res = super().action_confirm()
        if self.ignore:
            return True
        else:
            return res

    def _action_ignore(self):
        self.related_model_id.ignore_exception = True
        super()._action_ignore()
        return True
