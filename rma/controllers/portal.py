# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values['rma_count'] = request.env['rma.rma'].search_count([
        ])
        return values

    def _rma_get_page_view_values(self, rma, access_token, **kwargs):
        values = {
            'rma': rma,
            'current_date': fields.Datetime.now(),
        }
        return self._get_page_view_values(rma, access_token, values, 'my_rma_history', True, **kwargs)

    @http.route(['/my/rma', '/my/rma/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_rma(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        RMA = request.env['rma.rma']

        domain = []
        fields = ['name', 'create_date']

        archive_groups = self._get_archive_groups('rma.rma', domain, fields)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'confirmed', 'done', 'cancel'])]},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'purchase': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        rma_count = RMA.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/rma",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rma_count,
            page=page,
            step=self._items_per_page
        )
        # search the rmas to display, according to the pager data
        rmas = RMA.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_rma_history'] = rmas.ids[:100]

        rma_templates = request.env['rma.template'].sudo().search([('portal_ok', '=', True)])

        values.update({
            'request': request,
            'date': date_begin,
            'rma_list': rmas,
            'rma_templates': rma_templates,
            'page_name': 'rma',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/rma',
        })
        return request.render("rma.portal_my_rma", values)

    @http.route(['/my/rma/<int:rma_id>'], type='http', auth="public", website=True)
    def portal_my_rma_rma(self, rma_id=None, access_token=None, **kw):
        try:
            rma_sudo = self._document_check_access('rma.rma', rma_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._rma_get_page_view_values(rma_sudo, access_token, **kw)
        return request.render("rma.portal_my_rma_rma", values)

    @http.route(['/my/rma/new/<int:rma_template_id>',
                 '/my/rma/new/<int:rma_template_id>/res/<int:res_id>'], type='http', auth='public', website=True)
    def portal_rma_new(self, rma_template_id=None, res_id=None, **kw):
        if request.env.user.has_group('base.group_public'):
            return request.redirect('/my')

        rma_template = request.env['rma.template'].sudo().browse(rma_template_id)
        if not rma_template.exists() or not rma_template.portal_ok:
            return request.redirect('/my')

        error = None
        try:
            if res_id:
                # Even if res_id is not important to the RMA type, some sort of number
                # should be submitted to indicate that a selection has occurred.
                rma = rma_template._portal_try_create(request.env.user, res_id, **kw)
                if rma:
                    return request.redirect('/my/rma/' + str(rma.id))
        except ValidationError as e:
            error = e.name

        template_name = rma_template._portal_template(res_id=res_id)
        if not template_name:
            return request.redirect('/my')
        values = rma_template._portal_values(request.env.user, res_id=res_id)
        values.update({
            'request': request,
            'error': error,
            'current_date': fields.Datetime.now(),
        })
        return request.render(template_name, values)
