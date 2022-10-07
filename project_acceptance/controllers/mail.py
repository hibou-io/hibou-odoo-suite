from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers import mail


class PortalChatter(mail.PortalChatter):

    @http.route()
    def portal_chatter_post(self, res_model, res_id, message, attachment_ids='', attachment_tokens='', **kwargs):
        if request.httprequest.method == 'POST':
            task = request.env['project.task'].browse([res_id])
            # try:
            #     task_sudo = self._document_check_access('project.task', res_id, access_token=access_token)
            # except (AccessError, MissingError):
            #     return {'error': _('Invalid task.')}
            task.sudo().with_context(skip_detect_exceptions=True).write({'task_acceptance': 'feedback'})
            # task_sudo.with_context(skip_detect_exceptions=True).write({'task_acceptance': 'feedback'})
            # task_sudo.ignore_exception = True
            # task_sudo.task_acceptance = 'feedback'
            # task_sudo.ignore_exception = False

        return super(PortalChatter, self).portal_chatter_post(res_model, res_id, message, attachment_ids=attachment_ids, attachment_tokens=attachment_tokens, **kwargs)
