# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import requests
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HRPayrollPublisherUpdate(models.Model):
    _name = 'hr.payroll.publisher.update'
    _description = 'Payroll Update'
    _order = 'id DESC'
    
    def _default_request_modules(self):
        request_modules = self.env.context.get('default_request_modules')
        if not request_modules:
            request_modules = '\n'.join(self.env['publisher_warranty.contract'].hibou_payroll_modules_to_update())
        return request_modules
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('result', 'Result'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='draft')
    request_modules = fields.Char(default=_default_request_modules,
                                  states={'done': [('readonly', True)],
                                          'error': [('readonly', True)]})
    result = fields.Text(readonly=True)
    parameter_codes_retrieved = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    
    @api.model
    def cron_payroll_update(self):
        update = self.create({})
        if update.request_modules:
            update.button_send()
        else:
            update.unlink()
    
    def button_send(self):
        self.ensure_one()
        if not self.request_modules:
            raise UserError('One or more modules needed.')
        if self.result:
            raise UserError('Already retrieved')
        self._send()
        if self.result and not self.state == 'error':
            self._process_result()
    
    def _send(self):
        try:
            self.env['publisher_warranty.contract'].hibou_payroll_update(self)
        except UserError as e:
            self.set_error_state(e.name)
    
    def set_error_state(self, message=''):
        self.write({
            'state': 'error',
            'error': message,
        })
    
    def set_result(self, result):
        self.write({
            'state': 'result',
            'result': result,
            'error': False,
        })
    
    def button_process_result(self):
        self.ensure_one()
        if not self.result:
            raise UserError('No Result to process.')
        self._process_result()
    
    def _process_result(self):
        try:
            result_dict = json.loads(self.result)
            parameter_values = result_dict.get('payroll_parameter_values')
            if not parameter_values or not isinstance(parameter_values, list):
                self.set_error_state('Result is missing expected parameter values.')
            parameter_map = {}
            parameter_model = self.env['hr.rule.parameter'].sudo()
            for code, date_from, pv in parameter_values:
                date_from = fields.Date.from_string(date_from)
                if code not in parameter_map:
                    parameter_map[code] = parameter_model.search([('code', '=', code)], limit=1)
                parameter = parameter_map[code]
                if not parameter or parameter.update_locked:
                    continue
                # watch out for versions of Odoo where this is not datetime.date
                parameter_version = parameter.parameter_version_ids.filtered(lambda p: p.date_from == date_from)
                if not parameter_version:
                    parameter.write({
                        'parameter_version_ids': [(0, 0, {
                            'date_from': date_from,
                            'parameter_value': pv,
                        })]
                    })
                elif parameter_version.parameter_value != pv:
                    parameter_version.write({
                        'parameter_value': pv,
                    })
            # We have applied all of the updates. Set statistics.
            self.write({
                'state': 'done',
                'error': '',
                'parameter_codes_retrieved': '\n'.join('%s%s' % (c, '' if p and not p.update_locked else ' (LOCKED)' if p.update_locked else ' (MISSING)') for c, p in parameter_map.items()),
            })
        except Exception as e:
            self.set_error_state(str(e))


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = 'publisher_warranty.contract'
    
    CONFIG_HIBOU_URL_PAYROLL = 'https://api.hibou.io/hibouapi/v1/professional/payroll'

    @api.model
    def hibou_payroll_modules_to_update(self):
        # Filled downstream
        return []
    
    @api.model
    def hibou_payroll_update(self, update_request):
        # Check status locally
        status = self.hibou_professional_status()
        if status['expired']:
            raise UserError('Hibou Professional Subscription Expired, you cannot retrieve updates.')
        if status['expiration_reason'] == 'trial':
            raise UserError('Hibou Professional Subscription Trial, not eligible for updates.')
        if not status['professional_code']:
            raise UserError('Hibou Professional Subscription Missing, please setup your subscription.')
        
        if self.env.context.get('test_payroll_update_result'):
            update_request.set_result(self.env.context.get('test_payroll_update_result'))
            return
        
        try:
            res = self._hibou_payroll_update(update_request.request_modules)
            if res.get('error'):
                update_request.set_error_state(str(res.get('error')))
            else:
                update_request.set_result(json.dumps(res))
        except Exception as e:
            update_request.set_error_state(str(e))
        

    def _hibou_payroll_update(self, payroll_modules):
        data = self._get_hibou_message()
        data['payroll_modules'] = payroll_modules
        data = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': data,
        }
        r = requests.post(self.CONFIG_HIBOU_URL_PAYROLL, json=data, timeout=30)
        r.raise_for_status()
        wrapper = r.json()
        return wrapper.get('result', {})
