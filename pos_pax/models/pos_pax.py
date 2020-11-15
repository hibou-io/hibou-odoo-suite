# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, fields, api, _


class PoSPayment(models.Model):
    _inherit = 'pos.payment'

    pax_card_number = fields.Char(string='Card Number', help='Masked credit card.')
    pax_txn_id = fields.Char(string='PAX Transaction ID')


class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PoSPaymentMethod, self)._get_payment_terminal_selection() + [('pax', 'PAX')]


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pax_endpoint = fields.Char(string='PAX Endpoint',
                               help='Endpoint for PAX device (include protocol (http or https) and port). '
                                    'e.g. http://192.168.1.101:10009')


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        fields.update({
            'pax_card_number': ui_paymentline.get('pax_card_number'),
            'pax_txn_id': ui_paymentline.get('pax_txn_id'),
        })
        return fields
