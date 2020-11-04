from datetime import date, timedelta

import requests
import werkzeug

from odoo import models, api, service
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, misc


class ElavonTransaction(models.Model):
    _name = 'pos_elavon.elavon_transaction'

    def _get_pos_session(self):
        pos_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        if not pos_session:
            raise UserError(_("No opened point of sale session for user %s found") % self.env.user.name)

        pos_session.login()

        return pos_session

    def _get_pos_elavon_config_id(self, config, journal_id):
        journal = config.journal_ids.filtered(lambda r: r.id == journal_id)

        if journal and journal.pos_elavon_config_id:
            return journal.pos_elavon_config_id
        else:
            raise UserError(_("No Elavon configuration associated with the journal."))

    def _setup_request(self, data):
        # todo: in master make the client include the pos.session id and use that
        pos_session = self._get_pos_session()

        config = pos_session.config_id

        pos_elavon_config = self._get_pos_elavon_config_id(config, data['journal_id'])

        data['ssl_merchant_id'] = pos_elavon_config.sudo().merchant_id
        data['ssl_user_id'] = pos_elavon_config.sudo().merchant_user_id
        # Load from team
        data['ssl_pin'] = config.sudo().crm_team_id.pos_elavon_merchant_pin
        data['ssl_show_form'] = 'false'
        data['ssl_result_format'] = 'ascii'


    def _do_request(self, data):
        if not data['ssl_merchant_id'] or not data['ssl_user_id'] or not data['ssl_pin']:
            return "not setup"
        response = ''

        url = 'https://api.convergepay.com/VirtualMerchant/process.do'
        if self.env['ir.config_parameter'].sudo().get_param('pos_elavon.enable_test_env'):
            url = 'https://api.demo.convergepay.com/VirtualMerchantDemo/process.do'

        try:
            r = requests.post(url, data=data, timeout=500)
            r.raise_for_status()
            response = werkzeug.utils.unescape(r.content.decode())
        except Exception:
            response = "timeout"

        return response

    def _do_reversal_or_voidsale(self, data, is_voidsale):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        # Can we voidsale?
        #data['is_voidsale'] = is_voidsale
        data['ssl_transaction_type'] = 'CCVOID'
        response = self._do_request(data)
        return response

    @api.model
    def do_payment(self, data):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        data['ssl_transaction_type'] = 'CCSALE'
        response = self._do_request(data)
        return response

    @api.model
    def do_reversal(self, data):
        return self._do_reversal_or_voidsale(data, False)

    @api.model
    def do_voidsale(self, data):
        return self._do_reversal_or_voidsale(data, True)

    @api.model
    def do_return(self, data):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        data['ssl_transaction_type'] = 'CCRETURN'
        response = self._do_request(data)
        return response

    @api.model
    def do_credit(self, data):
        try:
            self._setup_request(data)
        except UserError:
            return "internal error"

        data['ssl_transaction_type'] = 'CCCREDIT'
        response = self._do_request(data)
        return response

    # One time (the ones we use) Elavon tokens are required to be
    # deleted after 6 months
    # This is a from Mercury, probably not needed anymore.
    @api.model
    def cleanup_old_tokens(self):
        expired_creation_date = (date.today() - timedelta(days=6 * 30)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        for order in self.env['pos.order'].search([('create_date', '<', expired_creation_date)]):
            order.ref_no = ""
            order.record_no = ""
