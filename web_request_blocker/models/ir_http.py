from odoo import models
from odoo.http import request
from werkzeug.exceptions import Forbidden
import re


KEY = 'web_request_blocker.user_agent_pattern'
FORCE_KEY = 'web_request_blocker.force_user_agent_pattern'

from odoo.tools import config
from os import environ
# Can't use config._env_options for undeclared option

EXTERNAL_PATTERN = environ.get(KEY) or config.options.get(KEY)
IGNORE_ICP = environ.get(FORCE_KEY) or config.options.get(FORCE_KEY)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _match(cls, path_info, key=None):
        # re and _get_param both handle their own caching!
        ICP = request.env['ir.config_parameter'].sudo()
        pattern = (not IGNORE_ICP and ICP._get_param(KEY)) or EXTERNAL_PATTERN
        user_agent = request and request.httprequest.environ.get('HTTP_USER_AGENT')
        if pattern and user_agent and re.match(pattern, user_agent):
            raise Forbidden()
        return super()._match(path_info, key)
