# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, models, fields


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('account.analytic.line', 'AnalyticLine'),
        ],
        ondelete={
            'account.analytic.line': 'cascade',
        },
    )
    timesheet_ids = fields.Many2many(
        'account.analytic.line',
        string="Timesheet")


class AnalyticLine(models.Model):
    _inherit = ['account.analytic.line', 'base.exception']
    _name = 'account.analytic.line'
    _order = 'main_exception_id asc'

    @api.model
    def create(self, values):
        res = super().create(values)
        res.detect_exceptions()
        return res

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(AnalyticLine, self)._exception_rule_eval_context(rec)
        res['timesheet'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'timesheet_ids'

    def write(self, vals):
        if not vals.get('ignore_exception'):
            for timesheet in self:
                if timesheet.detect_exceptions():
                    return self._popup_exceptions()
        return super().write(vals)

    @api.model
    def _get_popup_action(self):
        return self.env.ref('timesheet_exception.action_timesheet_exception_confirm')
    
    def detect_exceptions(self):
        res = False
        if not self._context.get("detect_exceptions"):
            self = self.with_context(detect_exceptions=True)
            res = super(AnalyticLine, self).detect_exceptions()
        return res
