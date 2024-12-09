# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Source IP for case creation - determination attempted at order creation and, if necessary, at confirmation
    def _get_source_ip(self):
        if request:
            return request.httprequest.environ['REMOTE_ADDR']
        return ''

    signifyd_case_id = fields.Many2one('signifyd.case', readonly=1, copy=False)
    singifyd_score = fields.Float(related='signifyd_case_id.score')
    signifyd_checkpoint_action = fields.Selection(string='Signifyd Action', related='signifyd_case_id.checkpoint_action')
    source_ip = fields.Char(default=_get_source_ip, copy=False, help='IP address of the customer, used for signifyd case creation.')

    def action_view_signifyd_case(self):
        self.ensure_one()
        if not self.signifyd_case_id:
            raise UserError('This order has no Signifyd Case')
        form_id = self.env.ref('website_sale_signifyd.signifyd_case_form_view').id
        context = {'create': False, 'delete': False}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Signifyd Case',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'res_model': 'signifyd.case',
            'res_id': self.signifyd_case_id.id,
            'context': context,
        }

    def action_confirm(self):
        res = super().action_confirm()
        if not self.source_ip:
            self.source_ip = self._get_source_ip()
        for sale in self.filtered(lambda so: so._should_post_signifyd()):
            _case = sale.post_signifyd_case()
        return res

    def _should_post_signifyd(self):
        # If we have no transaction/acquirer we will still send!
        # this case is useful for admin or free orders but could be customized here.
        acquirers = self.transaction_ids.acquirer_id
        if acquirers and not any(acquirers.mapped('signifyd_case_required')):
            return False
        if not self.website_id.signifyd_connector_id:
            return False
        if not self.source_ip:
            _logger.warning(f'{self.name}: no source IP for Signifyd Case creation')
            return False
        return True

    def post_signifyd_case(self):
        self.ensure_one()
        signifyd_api = self.website_id.signifyd_connector_id.get_connection()

        # Session values for Signifyd post
        if request and request.session:
            checkout_token = request.session.session_token
            order_session_id = checkout_token
        else:
            checkout_token = ''
        sig_vals = self._prepare_signifyd_case_values(order_session_id, checkout_token, self.source_ip)

        response = signifyd_api.post_case(sig_vals)
        case_id = response.get('signifydId')
        
        if not case_id:
            _logger.warning(f'{self.name}: Signifyd Case creation failed')
            return None

        new_case = self.env['signifyd.case'].create({
            'connector_id': self.website_id.signifyd_connector_id.id,
            'order_id': self.id,
            'partner_id': self.partner_id.id,
            'name': f'{self.name} ({case_id})',
            'case_id': case_id,
            'ref': response.get('orderId'),
            # Unused response fields in async mode:
            # decision
            # coverage
        })
        self.write({'signifyd_case_id': new_case.id})
        return new_case
    
    def _get_coverage_types(self):
        coverage_none = self.env.ref('website_sale_signifyd.signifyd_coverage_none')
        coverage_all = self.env.ref('website_sale_signifyd.signifyd_coverage_all')
        acquirer_coverage_types = self.transaction_ids.acquirer_id.signifyd_coverage_ids
        # 'ALL' if specified by any acquirer
        if coverage_all in acquirer_coverage_types:
            return coverage_all
        # 'NONE' if specified by all acquirers
        if acquirer_coverage_types and all(self.transaction_ids.acquirer_id.mapped(lambda a: a.signifyd_coverage_ids == coverage_none)):
            return coverage_none
        # Specific acquirer-level coverage types
        if acquirer_coverage_types - coverage_none:
            return acquirer_coverage_types - coverage_none
        # Default: connector-level
        return self.website_id.signifyd_connector_id.signifyd_coverage_ids or coverage_none

    @api.model
    def _prepare_signifyd_case_values(self, order_session_id, checkout_token, browser_ip_address):
        coverage_codes = self._get_coverage_types().mapped('code')

        # decision_request = self.website_id.signifyd_connector_id.signifyd_case_type or 'DECISION'

        # # find the highest 'acquirer override'
        # # note that we shouldn't be here if the override would prevent sending
        # a_case_types = self.transaction_ids.mapped('acquirer_id.signifyd_case_type')
        # if a_case_types and 'GUARANTEE' in a_case_types:
        #     decision_request = 'GUARANTEE'
        # elif a_case_types and 'SCORE' in a_case_types:
        #     decision_request = 'SCORE'
        # elif a_case_types and 'DECISION' in a_case_types:
        #     decision_request = 'DECISION'

        tx_status_type = {
            'draft': 'FAILURE',
            'pending': 'PENDING',
            'authorized': 'SUCCESS',
            'done': 'SUCCESS',
            'cancel': 'FAILURE',
            'error': 'ERROR',
        }
        recipients = self.partner_invoice_id + self.partner_shipping_id

        # API v3 WIP
        new_case_vals = {
            'orderId': self.name,
            'purchase': {
                'createdAt': self.date_order.isoformat(timespec='seconds') + '+00:00',
                'orderChannel': 'WEB',
                'totalPrice': self.amount_total,
                'totalShippingCost': self.amount_delivery,
                # TODO: check - previously used partner_id.currency_id, but then wouldn't the amount_total be in the wrong currency?
                'currency': self.currency_id.name,
                'confirmationEmail': self.partner_id.email,
                'confirmationPhone': self.partner_id.phone,
                'products': [
                    {
                        'itemName': line.product_id.name,
                        'itemPrice': line.price_unit,
                        'itemQuantity': line.product_uom_qty,
                        'itemIsDigital': line.product_id.is_digital,
                        'itemCategory': line.product_id.categ_id.name,
                        # 'itemSubCategory'?
                        'itemId': line.product_id.id,
                        'itemUrl': line.product_id.website_url,
                        'itemWeight': line.product_id.weight,
                    } for line in self.order_line if line.product_id
                ],
                'shipments': [{
                    'destination': {
                        'fullName': self.partner_shipping_id.name,
                        'organization': self.partner_shipping_id.commercial_partner_id.name or '',
                        # 'email': self.partner_shipping_id.email,
                        # 'phone': self.partner_shipping_id.phone,
                        'address': {
                            'streetAddress': self.partner_shipping_id.street or '',
                            'unit': self.partner_shipping_id.street2 or '',
                            'postalCode': self.partner_shipping_id.zip or '',
                            'city': self.partner_shipping_id.city or '',
                            'provinceCode': self.partner_shipping_id.state_id.code or '',
                            'countryCode': self.partner_shipping_id.country_id.code or ''
                        }
                    },
                    'carrier': self.carrier_id.name or '',
                    'fulfillmentMethod': self.carrier_id.signifyd_fulfillment_method,
                }],
            },
            'coverageRequests': coverage_codes,
            'transactions': [
                {
                    'parentTransactionId': None,
                    'transactionId': tx.id,
                    'gateway': tx.acquirer_id.name,
                    'paymentMethod': 'CREDIT_CARD',
                    'gatewayStatusCode': tx_status_type.get(tx.state, 'PENDING'),
                    'currency': tx.currency_id.name,
                    'amount': tx.amount,
                    # "avsResponseCode": "Y",
                    # "cvvResponseCode": "N",
                    'checkoutPaymentDetails': {
                        'accountHolderName': tx.partner_id.name,
                        'billingAddress': {
                            'streetAddress': tx.partner_id.street,
                            'unit': tx.partner_id.street2,
                            'city': tx.partner_id.city,
                            'provinceCode': tx.partner_id.state_id.code,
                            'postalCode': tx.partner_id.zip,
                            'countryCode': tx.partner_id.country_id.code,
                        }
                    }
                }
                for tx in self.transaction_ids
            ],
        }

        for line in new_case_vals['purchase']['products']:
            optional_keys = ['itemUrl', 'itemWeight']
            for key in optional_keys:
                if not line[key]:
                    line.pop(key)

        # API v2
        # new_case_vals = {
        #     'decisionRequest': {
        #         'paymentFraud': decision_request,
        #     },
        #     'purchase': {
        #         "orderSessionId": order_session_id,
        #         "orderId": self.id,
        #         "checkoutToken": checkout_token,
        #         "browserIpAddress": browser_ip_address,
        #         "currency": self.partner_id.currency_id.name,
        #         "orderChannel": "WEB",
        #         "totalPrice": self.amount_total,
        #         'products': [
        #             {
        #                 "itemId": line.product_id.id,
        #                 "itemName": line.product_id.name,
        #                 "itemIsDigital": False,
        #                 "itemCategory": line.product_id.categ_id.name,
        #                 "itemUrl": line.product_id.website_url or '',
        #                 "itemQuantity": line.product_uom_qty,
        #                 "itemPrice": line.price_unit,
        #                 "itemWeight": line.product_id.weight or 0.1,
        #             }
        #             for line in self.order_line if line.product_id
        #         ],
        #         'shipments': [{
        #                 "shipper": carrier.name,
        #                 "shippingMethod": "ground",
        #                 "shippingPrice": self.amount_delivery,
        #             }
        #             for carrier in self.carrier_id
        #         ],
        #     },
        #     'recipients': [
        #         {
        #             "fullName": partner.name,
        #             "confirmationEmail": partner.email,
        #             "confirmationPhone": partner.phone,
        #             "organization": partner.company_id.name,
        #             "deliveryAddress": {
        #                 "streetAddress": partner.street,
        #                 "unit": partner.street2,
        #                 "city": partner.city,
        #                 "provinceCode": partner.state_id.code,
        #                 "postalCode": partner.zip,
        #                 "countryCode": partner.country_id.code,
        #             }
        #         }
        #         for partner in recipients
        #     ],
        #     'transactions': [
        #         {
        #             "parentTransactionId": None,
        #             "transactionId": tx.id,
        #             "gateway": tx.acquirer_id.name,
        #             "paymentMethod": "CREDIT_CARD",
        #             "gatewayStatusCode": tx_status_type.get(tx.state, 'PENDING'),
        #             "type": "AUTHORIZATION",
        #             "currency": self.partner_id.currency_id.name,
        #             "amount": tx.amount,
        #             # "avsResponseCode": "Y",
        #             # "cvvResponseCode": "N",
        #             "checkoutPaymentDetails": {
        #                 "holderName": tx.partner_id.name,
        #                 "billingAddress": {
        #                     "streetAddress": tx.partner_id.street,
        #                     "unit": tx.partner_id.street2,
        #                     "city": tx.partner_id.city,
        #                     "provinceCode": tx.partner_id.state_id.code,
        #                     "postalCode": tx.partner_id.zip,
        #                     "countryCode": tx.partner_id.country_id.code,
        #                 }
        #             }
        #         }
        #         for tx in self.transaction_ids
        #     ],
        # }

        return new_case_vals
