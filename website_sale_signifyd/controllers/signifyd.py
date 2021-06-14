import json
from odoo.http import Controller, request, route
from odoo.http import Response


class SignifydWebhooks(Controller):

    @route(['/signifyd/cases/update'], type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def case_update(self, *args, **post):
        return self._case_update()

    def _case_update(self):
        data = json.loads(request.httprequest.data)
        vals = request.env['signifyd.connector'].process_post_values(data)
        case = self._get_case(vals.get('case_id'))
        if case:
            case.update_case_info(vals)
            return Response({'response': 'success'}, status=200, mimetype='application/json')
        return Response({'response': 'failed'}, status=500, mimetype='application/json')

    def _get_case(self, case_id):
        return request.env['signifyd.case'].sudo().search([('case_id', '=', case_id)], limit=1)
