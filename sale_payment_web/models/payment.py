from odoo import api, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def create(self, values):
        active_ids = self._context.get('active_ids')
        if active_ids and self._context.get('active_model') == 'sale.order':
            values['sale_order_ids'] = [(6, 0, active_ids)]
        return super(PaymentTransaction, self).create(values)
