# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import json
from odoo.http import Controller, request, route
from werkzeug.exceptions import NotFound


class SignifydWebhooks(Controller):

    @route(['/signifyd/cases/update'], type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def case_update(self, *args, **post):
        return self._case_update()

    def _case_update(self):
        data = json.loads(request.httprequest.data)

        case_id = data.get('signifydId')
        if not case_id:
            # Testing webhook
            return {'response': 'success'}

        case = self._get_case(case_id)
        if not case:
            raise NotFound('CaseId: %s Cannot be found.' % (case_id,))

        case.connector_id._check_webhook_signature(request)

        case.update_case_info(data)
        return {'response': 'success'}

    def _get_case(self, case_id):
        return request.env['signifyd.case'].sudo().search([('case_id', '=', case_id)], limit=1)
