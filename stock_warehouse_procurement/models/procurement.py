from odoo import models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    def _get_orderpoint_domain(self, company_id=False):
        domain = super(ProcurementGroup, self)._get_orderpoint_domain(company_id)
        warehouse_id = self.env.context.get('warehouse_id', None)
        if warehouse_id:
            domain.append(('warehouse_id', '=', warehouse_id))
        return domain
