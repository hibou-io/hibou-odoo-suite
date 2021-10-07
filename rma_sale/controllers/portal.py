# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from operator import itemgetter

import odoo.addons.rma.controllers.portal as rma_portal
from odoo.http import request
from odoo.tools.translate import _
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem

original_rma_portal_searchbar_filters = rma_portal.rma_portal_searchbar_filters
original_rma_portal_searchbar_inputs = rma_portal.rma_portal_searchbar_inputs
original_rma_portal_search_domain = rma_portal.rma_portal_search_domain
original_rma_portal_searchbar_groupby = rma_portal.rma_portal_searchbar_groupby
original_rma_portal_group_rmas = rma_portal.rma_portal_group_rmas


def rma_portal_searchbar_filters():
    res = original_rma_portal_searchbar_filters()
    res['sale'] = {'label': _('Sale Order'), 'domain': [('sale_order_id', '!=', False)]}
    return res


def rma_portal_searchbar_inputs():
    res = original_rma_portal_searchbar_inputs()
    res['sale'] = {'input': 'sale', 'label': _('Search Sale Order')}
    return res


def rma_portal_search_domain(search_in, search):
    search_domain = original_rma_portal_search_domain(search_in, search)
    if search_in in ('sale', 'all'):
        search_domain = OR([search_domain, [('sale_order_id', 'ilike', search)]])
    return search_domain


def rma_portal_searchbar_groupby():
    res = original_rma_portal_searchbar_groupby()
    res['sale'] = {'input': 'sale', 'label': _('Sale Order')}
    return res


def rma_portal_group_rmas(rmas, groupby):
    if groupby == 'sale':
        return [request.env['rma.rma'].concat(*g) for k, g in groupbyelem(rmas, itemgetter('sale_order_id'))]
    return original_rma_portal_group_rmas(rmas, groupby)


rma_portal.rma_portal_searchbar_filters = rma_portal_searchbar_filters
rma_portal.rma_portal_searchbar_inputs = rma_portal_searchbar_inputs
rma_portal.rma_portal_search_domain = rma_portal_search_domain
rma_portal.rma_portal_searchbar_groupby = rma_portal_searchbar_groupby
rma_portal.rma_portal_group_rmas = rma_portal_group_rmas
