from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    signifyd_case_id = fields.Many2one('signifyd.case', readonly=1)
    singifyd_score = fields.Float(related='signifyd_case_id.score', readonly=1)
    signifyd_disposition_status = fields.Selection(related='signifyd_case_id.guarantee_disposition', tracking=True)

    def action_view_signifyd_case(self):
        self.ensure_one()
        form_id = self.env.ref('gcl_signifyd_connector.signifyd_case_form_view').id
        context = {'create': False, 'delete': False, 'id': self.signifyd_case_id.id}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Signifyd Case',
            'view_mode': 'form',
            'views': [(form_id, 'form')],
            'res_model': 'signifyd.case',
            'res_id': self.signifyd_case_id.id,
            'context': context,
        }

    def post_signifyd_case(self, order_session_id, checkout_token, browser_ip_address):
        # Session values for Signifyd post
        data = {
            'order_session_id': order_session_id,
            'checkout_token': checkout_token,
            'browser_ip_address': browser_ip_address,
        }
        sig_vals = self.prepare_signifyd_case_values(data)

        case_res = self.env['signifyd.case'].post_case(sig_vals)

        success_response = case_res.get('investigationId')
        if success_response:
            new_case = self.env['signifyd.case'].create({
                'order_id': self.id,
                'case_id': success_response,
                'name': success_response,
            })
            self.write({'signifyd_case_id': new_case.id})
            self.partner_id.write({
                'signifyd_case_ids': [(4, new_case.id)],
            })
            return new_case

    @api.model
    def prepare_signifyd_case_values(self, data):
        order_session_id = data.get('order_session_id')
        checkout_token = data.get('checkout_token')
        browser_ip_address = data.get('browser_ip_address')

        new_case_vals = {}

        new_case_vals['purchase'] = {
            "orderSessionId": order_session_id,
            "orderId": self.id,
            "checkoutToken": checkout_token,
            "browserIpAddress": browser_ip_address,
            "currency": self.partner_id.currency_id.name,
            "orderChannel": "WEB",
            "totalPrice": self.amount_total,
        }

        new_case_vals['purchase']['products'] = []
        for line in self.order_line:
            product = line.product_id
            vals = {
                "itemId": product.id,
                "itemName": product.name,
                "itemIsDigital": False,
                "itemCategory": product.categ_id.name,
                "itemUrl": product.website_url,
                "itemQuantity": line.product_uom_qty,
                "itemPrice": line.price_unit,
                "itemWeight": product.weight,
            }
            new_case_vals['purchase']['products'].append(vals)

        new_case_vals['purchase']['shipments'] = []
        if self.carrier_id:
            vals = {
                "shipper": self.carrier_id.name,
                "shippingMethod": "ground",
                "shippingPrice": self.amount_delivery,
            }
            new_case_vals['purchase']['shipments'].append(vals)

        new_case_vals['recipients'] = []
        recipients = [self.partner_invoice_id, self.partner_shipping_id]
        for partner in recipients:
            vals = {
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
            new_case_vals['recipients'].append(vals)

        new_case_vals['transactions'] = []
        # payment.transaction
        for tx in self.transaction_ids:
            tx_status_type = {
                'draft': 'FAILURE',
                'pending': 'PENDING',
                'authorized': 'SUCCESS',
                'done': 'SUCCESS',
                'cancel': 'FAILURE',
                'error': 'ERROR',
            }

            tx_status = tx_status_type[tx.state]

            vals = {
                "parentTransactionId": None,
                "transactionId": tx.id,
                "gateway": tx.acquirer_id.name,
                "paymentMethod": "CREDIT_CARD",
                "gatewayStatusCode": tx_status,
                "type": "AUTHORIZATION",
                "currency": self.partner_id.currency_id.name,
                "amount": tx.amount,
                "avsResponseCode": "Y",
                "cvvResponseCode": "N",
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
            new_case_vals['transactions'].append(vals)

        return new_case_vals
