# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import html
from odoo import api, fields, models


class ExceptionRuleConfirm(models.AbstractModel):
    _inherit = 'exception.rule.confirm'

    show_ignore_button = fields.Boolean('Allow User Ignore', compute='_compute_show_ignore_button')

    @api.depends('exception_ids')
    def _compute_show_ignore_button(self):
        for wiz in self:
            wiz.show_ignore_button = (self.env.user.has_group('base_exception_user.group_exception_rule_user') and
                                      all(wiz.exception_ids.mapped('allow_user_ignore')))

    def action_confirm(self):
        if self.ignore and 'message_ids' in self.related_model_id:
            exceptions_summary = '<ul>%s</ul>' % ''.join(
                ['<li>%s: <i>%s</i></li>' % tuple(map(html.escape, (e.name, e.description or ''))) for e in
                 self.exception_ids])
            msg = '<p><strong>Exceptions ignored:</strong></p>' + exceptions_summary
            self.related_model_id.message_post(body=msg)
        return super().action_confirm()


    def action_ignore(self):
        self.ensure_one()
        if self.show_ignore_button:
            if 'message_ids' in self.related_model_id:
                msg = '<p><strong>Exceptions ignored:</strong></p>' + self.related_model_id.exceptions_summary
                self.related_model_id.message_post(body=msg)
            return self._action_ignore()
        return False

    def _action_ignore(self):
        return {'type': 'ir.actions.act_window_close'}
