import json
from odoo.http import Controller, request, route
from odoo.http import Response


class SignifydWebhooks(Controller):
    @route(['/cases/creation'], type='json', auth='public', methods=['POST'], csrf=False)
    def case_creation(self, *args, **post):
        data = json.loads(request.httprequest.data)
        vals = request.env['signifyd.connector'].process_post_values(data)
        # Update case with info
        case = request.env['signifyd.case'].sudo().search([('case_id', '=', vals['case_id'])])
        if case:
            case.sudo().update_case_info(vals)
            # Request guarantee for case if eligible
            try:
                case.request_guarantee()
                if case.guarantee_requested and not case.guarantee_eligible:
                    # Only alert Signifyd to stop trying if we have at least tried once already
                    return Response({'response': 'success'}, status=200, mimetype='application/json')
                # TODO what would the return case be here?
            except:
                # Signifyd API will try again up to 15 times if a non-2** code is returned
                return Response({'response': 'failed'}, status=500, mimetype='application/json')
        # TODO what would the return case be here?

    @route(['/cases/update'], type='json', auth='public', methods=['POST'], csrf=False)
    def case_update(self, *args, **post):
        data = json.loads(request.httprequest.data)
        vals = request.env['signifyd.connector'].process_post_values(data)
        case = request.env['signifyd.case'].sudo().search([('case_id', '=', vals['case_id'])])
        if case:
            case.update_case_info(vals)

        outcome = vals.get('guarantee_disposition')
        if case and outcome == 'DECLINED':
            for user in request.env.company.signifyd_connector_id.notify_user_ids:
                case.sudo().create_notification(user, outcome)
        # TODO any return result?
