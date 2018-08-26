# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProcurementOrderpointConfirm(models.TransientModel):
    _inherit = 'procurement.orderpoint.compute'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    @api.multi
    def procure_calculation(self):
        if self.warehouse_id:
            self = self.with_context(warehouse_id=self.warehouse_id.id)
        return super(ProcurementOrderpointConfirm, self).procure_calculation()
