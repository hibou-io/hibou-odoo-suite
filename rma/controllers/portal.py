# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from operator import itemgetter

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


def rma_portal_searchbar_sortings():
    # Override to add more sorting
    return {
        'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
        'name': {'label': _('Name'), 'order': 'name asc, id asc'},
    }


def rma_portal_searchbar_filters():
    # Override to add more filters
    return {
        'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'confirmed', 'done', 'cancel'])]},
        'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
        'confirmed': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
        'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
        'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
    }


def rma_portal_searchbar_inputs():
    # Override to add more search fields
    return {
        'name': {'input': 'name', 'label': _('Search in Name')},
        'all': {'input': 'all', 'label': _('Search in All')},
    }


def rma_portal_searchbar_groupby():
    # Override to add more options for grouping
    return {
        'none': {'input': 'none', 'label': _('None')},
        'state': {'input': 'state', 'label': _('State')},
        'template': {'input': 'template', 'label': _('Type')},
    }


def rma_portal_search_domain(search_in, search):
    # Override if you added search inputs
    search_domain = []
    if search_in in ('name', 'all'):
        search_domain.append(('name', 'ilike', search))
    return search_domain


def rma_portal_group_rmas(rmas, groupby):
    # Override to check groupby and perform a different grouping
    if groupby == 'state':
        return [request.env['rma.rma'].concat(*g) for k, g in groupbyelem(rmas, itemgetter('state'))]
    if groupby == 'template':
        return [request.env['rma.rma'].concat(*g) for k, g in groupbyelem(rmas, itemgetter('template_id'))]
    return [rmas]


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
    def portal_my_rma(self, page=1, date_begin=None, date_end=None, sortby='date', filterby='all', groupby='none', search_in='all', search=None, **kw):
        values = self._prepare_portal_layout_values()

        searchbar_sortings = rma_portal_searchbar_sortings()
        searchbar_filters = rma_portal_searchbar_filters()
        searchbar_inputs = rma_portal_searchbar_inputs()
        searchbar_groupby = rma_portal_searchbar_groupby()

        if sortby not in searchbar_sortings:
            raise UserError(_("Unknown sorting option."))
        order = searchbar_sortings[sortby]['order']

        if filterby not in searchbar_filters:
            raise UserError(_("Unknown filter option."))
        domain = searchbar_filters[filterby]['domain']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        if search_in and search:
            domain += rma_portal_search_domain(search_in, search)

        RMA = request.env['rma.rma']
        rma_count = len(RMA.search(domain))
        pager = portal_pager(
            url="/my/rma",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in, 'search': search},
            total=rma_count,
            page=page,
            step=self._items_per_page
        )
        rmas = RMA.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_rma_history'] = rmas.ids[:100]

        rma_templates = request.env['rma.template'].sudo().search([('portal_ok', '=', True)])

        grouped_rmas = rma_portal_group_rmas(rmas, groupby)
        values.update({
            'rma_templates': rma_templates,
            'date': date_begin,
            'grouped_rmas': grouped_rmas,
            'page_name': 'rma',
            'default_url': '/my/rma',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
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
                    return request.redirect(rma.get_portal_url())
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
