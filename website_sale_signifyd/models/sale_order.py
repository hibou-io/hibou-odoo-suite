from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    signifyd_case_id = fields.Many2one('signifyd.case', readonly=1, copy=False)
    singifyd_score = fields.Float(related='signifyd_case_id.score')
    signifyd_disposition_status = fields.Selection(related='signifyd_case_id.guarantee_disposition')

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
        for sale in self.filtered(lambda so: so.state in ('sale', 'done') and not so.signifyd_case_id):
            _case = sale.post_signifyd_case()
        return res

    def post_signifyd_case(self):
        if not self.website_id.signifyd_connector_id:
            return
        browser_ip_address = request.httprequest.environ['REMOTE_ADDR']
        if request.session:
            checkout_token = request.session.session_token
            order_session_id = checkout_token
        else:
            checkout_token = ''
        # Session values for Signifyd post
        sig_vals = self._prepare_signifyd_case_values(order_session_id, checkout_token, browser_ip_address)

        case = self.env['signifyd.case'].post_case(self.website_id.signifyd_connector_id, sig_vals)

        success_response = case.get('investigationId')
        if success_response:
            new_case = self.env['signifyd.case'].create({
                'order_id': self.id,
                'case_id': success_response,
                'name': success_response,
                'partner_id': self.partner_id.id,
            })
            self.write({'signifyd_case_id': new_case.id})
            return new_case
        # TODO do we need to raise an exception?
        return None

    @api.model
    def _prepare_signifyd_case_values(self, order_session_id, checkout_token, browser_ip_address):
        tx_status_type = {
            'draft': 'FAILURE',
            'pending': 'PENDING',
            'authorized': 'SUCCESS',
            'done': 'SUCCESS',
            'cancel': 'FAILURE',
            'error': 'ERROR',
        }
        recipients = self.partner_invoice_id + self.partner_shipping_id
        new_case_vals = {
            'decisionRequest': {
                'paymentFraud': 'GUARANTEE',
            },
            'purchase': {
                "orderSessionId": order_session_id,
                "orderId": self.id,
                "checkoutToken": checkout_token,
                "browserIpAddress": browser_ip_address,
                "currency": self.partner_id.currency_id.name,
                "orderChannel": "WEB",
                "totalPrice": self.amount_total,
                'products': [
                    {
                        "itemId": line.product_id.id,
                        "itemName": line.product_id.name,
                        "itemIsDigital": False,
                        "itemCategory": line.product_id.categ_id.name,
                        "itemUrl": line.product_id.website_url or '',
                        "itemQuantity": line.product_uom_qty,
                        "itemPrice": line.price_unit,
                        "itemWeight": line.product_id.weight or 0.1,
                    }
                    for line in self.order_line if line.product_id
                ],
                'shipments': [{
                        "shipper": carrier.name,
                        "shippingMethod": "ground",
                        "shippingPrice": self.amount_delivery,
                    }
                    for carrier in self.carrier_id
                ],
            },
            'recipients': [
                {
                    "fullName": partner.name,
                    "confirmationEmail": partner.email,
                    "confirmationPhone": partner.phone,
                    "organization": partner.company_id.name,
                    "deliveryAddress": {
                        "streetAddress": partner.street,
                        "unit": partner.street2,
                        "city": partner.city,
                        "provinceCode": partner.state_id.code,
                        "postalCode": partner.zip,
                        "countryCode": partner.country_id.code,
                    }
                }
                for partner in recipients
            ],
            'transactions': [
                {
                    "parentTransactionId": None,
                    "transactionId": tx.id,
                    "gateway": tx.acquirer_id.name,
                    "paymentMethod": "CREDIT_CARD",
                    "gatewayStatusCode": tx_status_type.get(tx.state, 'PENDING'),
                    "type": "AUTHORIZATION",
                    "currency": self.partner_id.currency_id.name,
                    "amount": tx.amount,
                    # "avsResponseCode": "Y",
                    # "cvvResponseCode": "N",
                    "checkoutPaymentDetails": {
                        "holderName": tx.partner_id.name,
                        "billingAddress": {
                            "streetAddress": tx.partner_id.street,
                            "unit": tx.partner_id.street2,
                            "city": tx.partner_id.city,
                            "provinceCode": tx.partner_id.state_id.code,
                            "postalCode": tx.partner_id.zip,
                            "countryCode": tx.partner_id.country_id.code,
                        }
                    }
                }
                for tx in self.transaction_ids
            ],
        }

        return new_case_vals
