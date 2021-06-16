# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import json
from odoo.http import Controller, request, route
from odoo.exceptions import MissingError


class SignifydWebhooks(Controller):

    @route(['/signifyd/cases/update'], type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def case_update(self, *args, **post):
        return self._case_update()

    def _case_update(self):
        data = json.loads(request.httprequest.data)
        vals = request.env['signifyd.connector'].process_post_values(data)
        case_id = vals.get('case_id')
        case = self._get_case(case_id)
        if case:
            case.update_case_info(vals)
            return {'response': 'success'}
        if case_id == 1:
            # Special case when verifying webhook.
            return {'response': 'success'}
        raise MissingError('CaseId: %s Cannot be found.' % (case_id, ))

    def _get_case(self, case_id):
        return request.env['signifyd.case'].sudo().search([('case_id', '=', case_id)], limit=1)
