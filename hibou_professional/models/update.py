# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import datetime
import requests

from odoo import api, fields, models, release, _
from odoo.exceptions import UserError


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'

    CONFIG_HIBOU_URL = 'https://api.hibou.io/hibouapi/v1/professional'
    CONFIG_HIBOU_MESSAGE_URL = 'https://api.hibou.io/hibouapi/v1/professional/message'
    CONFIG_HIBOU_QUOTE_URL = 'https://api.hibou.io/hibouapi/v1/professional/quote'
    DAYS_ENDING_SOON = 7

    @api.model
    def hibou_professional_status(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        expiration_date = get_param('database.hibou_professional_expiration_date')
        expiration_reason = get_param('database.hibou_professional_expiration_reason')
        dbuuid = get_param('database.uuid')
        expiring = False
        expired = False
        if expiration_date:
            expiration_date_date = fields.Date.from_string(expiration_date)
            today = fields.Date.today()
            if expiration_date_date < today:
                if expiration_reason == 'trial':
                    expired = _('Your trial of Hibou Professional has ended.')
                else:
                    expired = _('Your Hibou Professional subscription has ended.')
            elif expiration_date_date < (today + datetime.timedelta(days=self.DAYS_ENDING_SOON)):
                if expiration_reason == 'trial':
                    expiring = _('Your trial of Hibou Professional is ending soon.')
                else:
                    expiring = _('Your Hibou Professional subscription is ending soon.')

        is_admin = self.env.user.has_group('base.group_erp_manager')
        allow_admin_message = get_param('database.hibou_allow_admin_message')
        allow_message = get_param('database.hibou_allow_message')

        return {
            'expiration_date': expiration_date,
            'expiration_reason': expiration_reason,
            'expiring': expiring,
            'expired': expired,
            'professional_code': get_param('database.hibou_professional_code'),
            'dbuuid': dbuuid,
            'is_admin': is_admin,
            'allow_admin_message': allow_admin_message,
            'allow_message': allow_message,
        }

    @api.model
    def hibou_professional_update_message_preferences(self, allow_admin_message, allow_message):
        if self.env.user.has_group('base.group_erp_manager'):
            set_param = self.env['ir.config_parameter'].sudo().set_param
            set_param('database.hibou_allow_admin_message', allow_admin_message and '1')
            set_param('database.hibou_allow_message', allow_message and '1')
        return self.hibou_professional_status()

    def _check_message_allow(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        allow_message = get_param('database.hibou_allow_message')
        if not allow_message:
            allow_message = get_param('database.hibou_allow_admin_message') and self.env.user.has_group(
                'base.group_erp_manager')
            if not allow_message:
                raise UserError(_('You are not allowed to send messages at this time.'))

    @api.model
    def hibou_professional_quote(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        try:
            self._hibou_install()
        except:
            pass
        dbuuid = get_param('database.uuid')
        dbtoken = get_param('database.hibou_token')
        if dbuuid and dbtoken:
            return {'url': self.CONFIG_HIBOU_QUOTE_URL + '/%s/%s' % (dbuuid, dbtoken)}
        return {}

    @api.model
    def hibou_professional_send_message(self, type, priority, subject, body, user_url, res_id):
        self._check_message_allow()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        dbuuid = get_param('database.uuid')
        dbtoken = get_param('database.hibou_token')
        user_name = self.env.user.name
        user_email = self.env.user.email or self.env.user.login
        company_name = self.env.user.company_id.name
        data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'dbuuid': dbuuid,
                'user_name': user_name,
                'user_email': user_email,
                'user_url': user_url,
                'company_name': company_name,
                'type': type,
                'priority': priority,
                'subject': subject,
                'body': body,
                'res_id': res_id,
            },
        }
        if dbtoken:
            data['params']['dbtoken'] = dbtoken
        try:
            r = requests.post(self.CONFIG_HIBOU_MESSAGE_URL + '/new', json=data, timeout=30)
            r.raise_for_status()
            wrapper = r.json()
            return wrapper.get('result', {})
        except:
            return {'error': _('Error sending message.')}

    @api.model
    def hibou_professional_get_messages(self):
        self._check_message_allow()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        dbuuid = get_param('database.uuid')
        dbtoken = get_param('database.hibou_token')
        try:
            r = requests.get(self.CONFIG_HIBOU_MESSAGE_URL + '/get/%s/%s' % (dbuuid, dbtoken), timeout=30)
            r.raise_for_status()
            # not jsonrpc
            return r.json()
        except:
            return {'error': _('Error retrieving messages, maybe the token is wrong.')}

    @api.model
    def hibou_professional_update(self, professional_code):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('database.hibou_professional_code', professional_code)
        try:
            self._hibou_install()
        except:
            pass
        return self.hibou_professional_status()

    def _get_hibou_modules(self):
        domain = [('state', 'in', ['installed', 'to upgrade', 'to remove']), ('author', 'ilike', 'hibou')]
        module_list = self.env['ir.module.module'].sudo().search_read(domain, ['name'])
        return {module['name']: 1 for module in module_list}

    def _get_hibou_message(self):
        IrParamSudo = self.env['ir.config_parameter'].sudo()

        dbuuid = IrParamSudo.get_param('database.uuid')
        dbtoken = IrParamSudo.get_param('database.hibou_token')
        db_create_date = IrParamSudo.get_param('database.create_date')
        user = self.env.user.sudo()
        professional_code = IrParamSudo.get_param('database.hibou_professional_code')

        module_dictionary = self._get_hibou_modules()
        modules = []
        for module, qty in module_dictionary.items():
            modules.append(module if qty == 1 else '%s,%s' % (module, qty))

        web_base_url = IrParamSudo.get_param('web.base.url')
        msg = {
            "dbuuid": dbuuid,
            "dbname": self._cr.dbname,
            "db_create_date": db_create_date,
            "version": release.version,
            "language": user.lang,
            "web_base_url": web_base_url,
            "modules": '\n'.join(modules),
            "professional_code": professional_code,
        }
        if dbtoken:
            msg['dbtoken'] = dbtoken
        msg.update({'company_' + key: value for key, value in user.company_id.read(["name", "email", "phone"])[0].items() if key != 'id'})
        return msg

    def _process_hibou_message(self, result):
        if result.get('professional_info'):
            set_param = self.env['ir.config_parameter'].sudo().set_param
            set_param('database.hibou_professional_expiration_date', result['professional_info'].get('expiration_date'))
            set_param('database.hibou_professional_expiration_reason', result['professional_info'].get('expiration_reason', 'trial'))
            if result['professional_info'].get('professional_code'):
                set_param('database.hibou_professional_code', result['professional_info'].get('professional_code'))
            if result['professional_info'].get('dbtoken'):
                set_param('database.hibou_token', result['professional_info'].get('dbtoken'))

    def _hibou_install(self):
        data = self._get_hibou_message()
        data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': data,
        }
        r = requests.post(self.CONFIG_HIBOU_URL, json=data, timeout=30)
        r.raise_for_status()
        wrapper = r.json()
        self._process_hibou_message(wrapper.get('result', {}))

    @api.model
    def _get_sys_logs(self):
        try:
            self._hibou_install()
        except:
            pass
        return super(PublisherWarrantyContract, self)._get_sys_logs()
