try:
    from markdown import markdown
except ImportError:
    markdown = None

from odoo import api, fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    name_markdown = fields.Html(compute='_compute_name_markdown')

    def _compute_name_markdown(self):
        if not markdown:
            for line in self:
                # Why not just name? Because it needs to be escaped.
                # Use nothing to indicate that it shouldn't be used.
                line.name_markdown = ''
        else:
            for line in self:
                line.name_markdown = markdown(line.name)
