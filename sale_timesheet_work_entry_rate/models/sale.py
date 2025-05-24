# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('analytic_line_ids.work_type_id')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()

    # Overridden to select work_type_id and do multiplication at the end
    def _get_delivered_quantity_by_analytic(self, additional_domain):
        """ Compute and write the delivered quantity of current SO lines, based on their related
            analytic lines.
            :param additional_domain: domain to restrict AAL to include in computation (required since timesheet is an AAL with a project ...)
        """
        result = {}

        # avoid recomputation if no SO lines concerned
        if not self:
            return result

        # group analytic lines by product uom and so line
        domain = expression.AND([[('so_line', 'in', self.ids)], additional_domain])
        data = self.env['account.analytic.line'].read_group(
            domain,
            ['so_line', 'unit_amount', 'product_uom_id', 'work_type_id'], ['product_uom_id', 'so_line', 'work_type_id'], lazy=False
        )

        # convert uom and sum all unit_amount of analytic lines to get the delivered qty of SO lines
        # browse so lines and product uoms here to make them share the same prefetch
        lines = self.browse([item['so_line'][0] for item in data])
        lines_map = {line.id: line for line in lines}
        product_uom_ids = [item['product_uom_id'][0] for item in data if item['product_uom_id']]
        product_uom_map = {uom.id: uom for uom in self.env['uom.uom'].browse(product_uom_ids)}
        work_type_ids = [item['work_type_id'][0] for item in data if item['work_type_id']]
        work_type_map = {work.id: work for work in self.env['hr.work.entry.type'].browse(work_type_ids)}
        for item in data:
            if not item['product_uom_id']:
                continue
            work_type_rate = False
            if item['work_type_id']:
                work_type_rate = work_type_map.get(item['work_type_id'][0]).timesheet_billing_rate
            if work_type_rate is False:
                # unset field should be 1.0 by default, you CAN set it to 0.0 if you'd like.
                work_type_rate = 1.0

            so_line_id = item['so_line'][0]
            so_line = lines_map[so_line_id]
            result.setdefault(so_line_id, 0.0)
            uom = product_uom_map.get(item['product_uom_id'][0])
            if so_line.product_uom.category_id == uom.category_id:
                qty = uom._compute_quantity(item['unit_amount'], so_line.product_uom, rounding_method='HALF-UP')
            else:
                qty = item['unit_amount']

            qty *= work_type_rate
            result[so_line_id] += qty

        return result
