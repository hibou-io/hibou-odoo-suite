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
            
            # this is mostly like session finalize() as we skip MFA
            env = http.request.env(user=user)
            user_context = dict(env['res.users'].context_get())

            http.request.session.should_rotate = True
            http.request.session.update({
                'login': user.login,
                'uid': user.id,
                'context': user_context,
                'session_token': env.user._compute_session_token(http.request.session.sid),
            })

            return http.request.redirect('/my/home')
        except (exceptions.Warning, ) as e:
            return http.Response(e.message, status=400)
