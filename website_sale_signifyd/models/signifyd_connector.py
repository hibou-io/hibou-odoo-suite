import requests
from datetime import datetime as dt
from base64 import b64encode
import json

from odoo import api, fields, models


class SignifydConnector(models.Model):
    _name = 'signifyd.connector'
    _description = 'Interact with Signifyd API'

    name = fields.Char(string='Connector Name')
    test_mode = fields.Boolean(string='Test Mode')
    user_key = fields.Char(string='Team/Username')
    secret_key = fields.Char(string='API Key')
    user_key_test = fields.Char(string='TEST Team/Username')
    secret_key_test = fields.Char(string='TEST API Key')
    webhooks_registered = fields.Boolean(string='Successfully Registered Webhooks')
    notify_user_ids = fields.Many2many('res.users', string='Receive decline notifications')

    # TODO ideally this would be a regular constant
    # however other entities currently use this by reference
    API_URL = 'https://api.signifyd.com/v2'

    def get_headers(self):
        self.ensure_one()
        # Check for prod or test mode
        if self.test_mode:
            api_key = self.secret_key_test
        else:
            api_key = self.secret_key

        b64_auth_key = b64encode(api_key.encode()).decode().replace('=', '')

        headers = {
            'Authorization': 'Basic ' + b64_auth_key,
            'Content-Type': 'application/json',
        }

        return headers

    def register_webhooks(self):
        self.ensure_one()
        headers = self.get_headers()
        # This should come from the website...
        # we may need a better way to link the connector to the website.
        base_url = None
        website = self.env['website'].search([('signifyd_connector_id', '=', self.id)], limit=1)
        if website and website.domain:
            base_url = website.domain
            if base_url.find('://') <= 0:  # documentation says if no protocol use http
                base_url = 'http://' + base_url
        if not base_url:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        values = {
            "webhooks": [
                # Given we are creating the cases, we do not need to know about it
                # {
                #     "event": "CASE_CREATION",
                #     "url": base_url + "/signifyd/cases/update"
                # },
                {
                    "event": "CASE_RESCORE",
                    "url": base_url + "/signifyd/cases/update"
                },
                {
                    "event": "CASE_REVIEW",
                    "url": base_url + "/signifyd/cases/update"
                },
                {
                    "event": "GUARANTEE_COMPLETION",
                    "url": base_url + "/signifyd/cases/update"
                },
            ]
        }
        data = json.dumps(values, indent=4)
        r = requests.post(
            self.API_URL + '/teams/webhooks',
            headers=headers,
            data=data,
        )
        # r.raise_for_status()
        return r

    def action_register_webhooks(self):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Signifyd Connector'),
                'sticky': True,
            },
        }

        res = self.register_webhooks()

        if 200 <= res.status_code < 300:
            notification['params']['type'] = 'success'
            notification['params']['message'] = 'Successfully registered webhooks with Signifyd.'
            self.webhooks_registered = True
            return notification

        else:
            notification['params']['type'] = 'danger'
            notification['params']['message'] = res.content.decode('utf-8')
            self.webhooks_registered = False
            return notification

    def process_post_values(self, post):
        # Construct dict from request data for endpoints
        uuid = post.get('uuid')
        case_id = post.get('caseId')
        team_name = post.get('teamName')
        team_id = post.get('teamId')
        review_disposition = post.get('reviewDisposition')
        guarantee_disposition = post.get('guaranteeDisposition')
        order_outcome = post.get('orderOutcome')
        status = post.get('status')
        score = post.get('score')
        disposition_reason = post.get('dispositionReason')
        disposition = post.get('disposition')
        last_update = str(dt.now())

        values = {}

        # Validate that the order and case match the request
        values.update({'uuid': uuid}) if uuid else ''
        values.update({'team_name': team_name}) if team_name else ''
        values.update({'team_id': team_id}) if team_id else ''
        values.update({'review_disposition': review_disposition}) if review_disposition else ''
        values.update({'guarantee_disposition': guarantee_disposition}) if guarantee_disposition else ''
        values.update({'order_outcome': order_outcome}) if order_outcome else ''
        values.update({'status': status}) if status else ''
        values.update({'score': score}) if score else ''
        values.update({'case_id': case_id}) if case_id else ''
        values.update({'disposition_reason': disposition_reason}) if disposition_reason else ''
        values.update({'disposition': disposition}) if disposition else ''
        values.update({'last_update': last_update})

        return values
