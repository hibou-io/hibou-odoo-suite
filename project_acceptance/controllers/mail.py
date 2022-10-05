from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers import mail


class PortalChatter(mail.PortalChatter):
    
    
    @http.route()
    def portal_chatter_post(self, res_model, res_id, message, attachment_ids='', attachment_tokens='', **kwargs):
        if request.httprequest.method == 'POST':
            task = request.env['project.task'].browse([res_id])
            task.sudo().ignore_exception = True
            task.sudo().task_acceptance = 'feedback'
            task.sudo().ignore_exception = False
        return super(PortalChatter, self).portal_chatter_post(res_model, res_id, message, attachment_ids=attachment_ids, attachment_tokens=attachment_tokens, **kwargs)
    