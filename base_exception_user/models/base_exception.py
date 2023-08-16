# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import html
from odoo import api, models, fields


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    allow_user_ignore = fields.Boolean('Allow User Ignore')


class BaseException(models.AbstractModel):
    _inherit = 'base.exception'

    @api.depends("exception_ids", "ignore_exception")
    def _compute_exceptions_summary(self):
        for rec in self:
            if rec.exception_ids and not rec.ignore_exception:
                rec.exceptions_summary = "<ul>%s</ul>" % "".join(
                    [
                        "<li>%s: <i>%s</i></li>"
                        % tuple(map(html.escape, (e.name, e.description or '')))
                        for e in rec.exception_ids
                    ]
                )
            else:
                rec.exceptions_summary = False
