from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request
from re import match, PatternError

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.constrains('value')
    def _check_user_agent_pattern(self):
        for icp in self.filtered(lambda p:
            p.key == 'web_request_blocker.user_agent_pattern' and p.value):
            try:
                current_user_agent = request and request.httprequest.environ.get('HTTP_USER_AGENT')
                if current_user_agent and match(icp.value, current_user_agent):
                    raise ValidationError(_('This pattern would lock you out!\n\nYour current user agent:\n%s', current_user_agent))
            except PatternError:
                raise ValidationError(_('Bad regex !'))
