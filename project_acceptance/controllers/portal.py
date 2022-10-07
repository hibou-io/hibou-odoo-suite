from odoo import fields, http, SUPERUSER_ID, _
from odoo.http import request

from odoo.addons.portal.controllers import portal

class CustomerPortal(portal.CustomerPortal):

    @http.route('/my/task/<int:task_id>/accept', type='http', auth="user", methods=['POST'], website=True)
    def portal_task_accept(self, task_id, access_token=None, **post):

        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid task.')}

        task_sudo.with_context(skip_detect_exceptions=True).write({'task_acceptance': 'accept'})
        # task_sudo.ignore_exception = True
        # task_sudo.task_acceptance = 'accept'
        # task_sudo.ignore_exception = False
        return request.redirect(task_sudo.get_portal_url())

    @http.route(['/my/task/<int:task_id>/decline'], type='http', methods=['POST'], auth="user", website=True)
    def portal_task_decline(self, task_id, access_token=None, **post):

        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid task.')}

        task_sudo.with_context(skip_detect_exceptions=True).write({'task_acceptance': 'decline'})
        # task_sudo.ignore_exception = True
        # task_sudo.task_acceptance = 'decline'
        # task_sudo.ignore_exception = False
        return request.redirect(task_sudo.get_portal_url())


    ######################################################################
    # The next code is for modal views and to sign document for acceptance
    #####################################################################
    # import binascii
    # from odoo.exceptions import AccessError, MissingError, ValidationError
    # from odoo.addons.portal.controllers.mail import _message_post_helper
    # from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
    
    # @http.route(['/my/task/<int:task_id>'], type='http', auth="public", website=True)
    # def portal_my_task(self, task_id, access_token=None, **kw):
    #     try:
    #         task_sudo = self._document_check_access('project.task', task_id, access_token)
    #     except (AccessError, MissingError):
    #         return request.redirect('/my')

    #     # ensure attachment are accessible with access token inside template
    #     for attachment in task_sudo.attachment_ids:
    #         attachment.generate_access_token()
    #     values = self._task_get_page_view_values(task_sudo, access_token, **kw)
    #     # return request.render("project.portal_my_task", values)
    #     return request.render('project_acceptance.portal_my_task_inherit', values)
    
    # @http.route(['/my/task/<int:task_id>/modaccept'], type='json', auth="public", website=True)
    # def portal_quote_accept(self, task_id, access_token=None, name=None, signature=None):
    #     # get from query string if not on json param
    #     access_token = access_token or request.httprequest.args.get('access_token')
    #     try:
    #         task_sudo = self._document_check_access('project.task', task_id, access_token=access_token)
    #     except (AccessError, MissingError):
    #         return {'error': _('Invalid order.')}

    #     if not task_sudo.has_to_be_signed():
    #         return {'error': _('The task is not in a state requiring customer signature.')}
    #     if not signature:
    #         return {'error': _('Signature is missing.')}

    #     try:
    #         task_sudo.write({
    #             'signed_by': name,
    #             'signed_on': fields.Datetime.now(),
    #             'signature': signature,
    #         })
    #         request.env.cr.commit()
    #     except (TypeError, binascii.Error) as e:
    #         return {'error': _('Invalid signature data.')}
        
    #     pdf = request.env.ref('project_task.action_report_project_task').with_user(SUPERUSER_ID)._render_qweb_pdf([task_sudo.id])[0]

    #     _message_post_helper(
    #         'project.task', task_sudo.id, _('Task signed by %s') % (name,),
    #         attachments=[('%s.pdf' % task_sudo.name, pdf)],
    #         **({'token': access_token} if access_token else {}))

    #     query_string = '&message=sign_ok'
    #     if task_sudo.has_to_be_paid(True):
    #         query_string += '#allow_payment=yes'
    #     return {
    #         'force_refresh': True,
    #         'redirect_url': task_sudo.get_portal_url(query_string=query_string),
    #     }

    # @http.route(['/my/task/<int:task_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    # def decline(self, task_id, access_token=None, **post):
    #     try:
    #         task_sudo = self._document_check_access('project.task', task_id, access_token=access_token)
    #     except (AccessError, MissingError):
    #         return request.redirect('/my')

    #     message = post.get('decline_message')

    #     query_string = False
    #     if task_sudo.has_to_be_signed() and message:
    #         task_sudo.action_cancel()
    #         _message_post_helper('project.task', task_id, message, **{'token': access_token} if access_token else {})
    #     else:
    #         query_string = "&message=cant_reject"

    #     return request.redirect(task_sudo.get_portal_url(query_string=query_string))
