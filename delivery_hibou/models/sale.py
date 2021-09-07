from odoo import api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def button_test_rate_multi(self):
        raise UserError(str(self.carrier_id.rate_shipment_multi(order=self)))
