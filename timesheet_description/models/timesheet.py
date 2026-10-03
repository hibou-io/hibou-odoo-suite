try:
    from markdown2 import markdown
except ImportError:
    markdown = None

from odoo import api, fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    name_markdown = fields.Html(compute='_compute_name_markdown')

    @api.depends("name")
    def _compute_name_markdown(self):
        for line in self:
            # Why not just name? Because it needs to be escaped.
            # Use nothing to indicate that it shouldn't be used.
            name_markdown = ""
            if markdown:
                name_markdown = markdown(line.name)
            line.name_markdown = name_markdown
