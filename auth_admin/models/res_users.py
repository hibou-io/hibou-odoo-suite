from odoo import models, api, exceptions
from odoo.http import request
from datetime import datetime
from time import mktime
import hmac
from hashlib import sha256

from logging import getLogger
_logger = getLogger(__name__)


def admin_auth_generate_login(env, user):
    """
    Generates a URL to allow the current user to login as the portal user.

    :param env: Odoo environment
    :param user: `res.users` in
    :return:
    """
    if not env['res.partner'].check_access_rights('write'):
        return None
    u = str(user.id)
    now = datetime.utcnow()
    fifteen = int(mktime(now.timetuple())) + (15 * 60)
    e = str(fifteen)
    o = str(env.uid)

    config = env['ir.config_parameter'].sudo()
    key = str(config.search([('key', '=', 'database.secret')], limit=1).value)
    h = hmac.new(key.encode(), (u + e + o).encode(), sha256)

    base_url = str(config.search([('key', '=', 'web.base.url')], limit=1).value)

    _logger.warn('login url for user id: ' + u + ' original user id: ' + o)

    return base_url + '/auth_admin?u=' + u + '&e=' + e + '&o=' + o + '&h=' + h.hexdigest()


def check_admin_auth_login(env, u_user_id, e_expires, o_org_user_id, hash_):
    """
    Checks that the parameters are valid and that the user exists.

    :param env: Odoo environment
    :param u_user_id: Desired user id to login as.
    :param e_expires: Expiration timestamp
    :param o_org_user_id: Original user id.
    :param hash_: HMAC generated hash
    :return: `res.users`
    """

    now = datetime.utcnow()
    now = int(mktime(now.timetuple()))
    fifteen = now + (15 * 60)

    config = env['ir.config_parameter'].sudo()
    key = str(config.search([('key', '=', 'database.secret')], limit=1).value)

    myh = hmac.new(key.encode(), str(str(u_user_id) + str(e_expires) + str(o_org_user_id)).encode(), sha256)

    if not hmac.compare_digest(hash_, myh.hexdigest()):
        raise exceptions.AccessDenied('Invalid Request')

    if not (now <= int(e_expires) <= fifteen):
        raise exceptions.AccessDenied('Expired')

    user = env['res.users'].sudo().search([('id', '=', int(u_user_id))], limit=1)
    if not user.id:
        raise exceptions.AccessDenied('Invalid User')
    return user


class ResUsers(models.Model):
    _inherit = 'res.users'

    def admin_auth_generate_login(self):
        self.ensure_one()

        login_url = admin_auth_generate_login(self.env, self)
        if login_url:
            raise exceptions.Warning(login_url)

        return False

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except exceptions.AccessDenied:
            if request and hasattr(request, 'session') and request.session.get('auth_admin'):
                _logger.warn('_check_credentials for user id: ' + \
                             str(request.session.uid) + ' original user id: ' + str(request.session.auth_admin))
            else:
                raise
