# -*- coding: utf-8 -*-

from odoo import models


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _get_orderpoint_domain(self, company_id=False):
        domain = super(ProcurementOrder, self)._get_orderpoint_domain(company_id)
        warehouse_id = self.env.context.get('warehouse_id', None)
        if warehouse_id:
            domain += [('warehouse_id', '=', warehouse_id)]
        return domain
