# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def send_to_shipper(self):
        if self.filtered(lambda p: p.carrier_tracking_ref):
            raise UserError(_('Unable to send to shipper with existing tracking numbers.'))
        return super(StockPicking, self).send_to_shipper()
