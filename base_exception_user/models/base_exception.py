from odoo import models, fields


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    allow_user_ignore = fields.Boolean('Allow User Ignore')
