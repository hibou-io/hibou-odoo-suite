from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_planning_policy_id = fields.Many2one('sale.order.planning.policy', company_dependent=True,
        string="Order Planner Policy",
        help="The Order Planner Policy to use when making a sale order planner.")

    def get_planning_policy(self):
        self.ensure_one()
        return self.property_planning_policy_id or self.categ_id.property_planning_policy_categ_id


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_planning_policy_categ_id = fields.Many2one('sale.order.planning.policy', company_dependent=True,
        string="Order Planner Policy",
        help="The Order Planner Policy to use when making a sale order planner.")
