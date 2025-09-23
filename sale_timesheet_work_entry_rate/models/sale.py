# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models


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
        result = defaultdict(float)

        # avoid recomputation if no SO lines concerned
        if not self:
            return result

        # group analytic lines by product uom and so line
        domain = fields.Domain.AND([[('so_line', 'in', self.ids)], additional_domain])
        data = self.env['account.analytic.line']._read_group(
            domain,
            ['so_line', 'unit_amount', 'product_uom_id', 'work_type_id'],
            ['move_line_id:count_distinct', '__count']
        )

        # convert uom and sum all unit_amount of analytic lines to get the delivered qty of SO lines
        # browse so lines and product uoms here to make them share the same prefetch
        for so_line, unit_amount, uom, work_type_id, move_line_id_count_distinct, count in data:
            if not uom:
                continue

            # avoid counting unit_amount twice when dealing with multiple analytic lines on the same move line
            if move_line_id_count_distinct == 1 and count > 1:
                qty = unit_amount / count
            else:
                qty = unit_amount
            qty = uom._compute_quantity(qty, so_line.product_uom_id, rounding_method='HALF-UP')

            work_type_rate = work_type_id.timesheet_billing_rate if work_type_id else 1.0
            qty *= work_type_rate
            result[so_line.id] += qty

        return result
