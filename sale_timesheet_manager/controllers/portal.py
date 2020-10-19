from odoo import _
from odoo.http import Controller, request, route
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from logging import getLogger as Logs
_logger = Logs(__name__)


class SaleTimesheetManager(Controller):
    @route('/my/task/time/manager', type='http', auth='public', website=True)
    def portal_my_timesheet_manager(self, **kwargs):
        user = request.env.user
        vals = {
            'user': user,
            'projects': user._get_tasks_grouped_by_project(),
        }

        return request.render('sale_timesheet_manager.dashboard', vals)
