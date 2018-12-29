from odoo import http, exceptions
from ..models.res_users import check_admin_auth_login

from logging import getLogger
_logger = getLogger(__name__)


class AuthAdmin(http.Controller):

    @http.route(['/auth_admin'], type='http', auth='public', website=True)
    def index(self, *args, **post):
        u = post.get('u')
        e = post.get('e')
        o = post.get('o')
        h = post.get('h')

        if not all([u, e, o, h]):
            exceptions.Warning('Invalid Request')

        u = str(u)
        e = str(e)
        o = str(o)
        h = str(h)

        try:
            user = check_admin_auth_login(http.request.env, u, e, o, h)

            http.request.session.uid = user.id
            http.request.session.login = user.login
            http.request.session.password = ''
            http.request.session.auth_admin = int(o)
            http.request.uid = user.id
            uid = http.request.session.authenticate(http.request.session.db, user.login, 'x')
            if uid is not False:
                http.request.params['login_success'] = True
                return http.redirect_with_hash('/my/home')
            return http.local_redirect('/my/home')
        except (exceptions.Warning, ) as e:
            return http.Response(e.message, status=400)
