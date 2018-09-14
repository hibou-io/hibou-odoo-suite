from odoo import api, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def send_to_shipper(self):
        res = False
        for pick in self.filtered(lambda p: not p.carrier_tracking_ref):
            res = super(StockPicking, pick).send_to_shipper()
        return res
