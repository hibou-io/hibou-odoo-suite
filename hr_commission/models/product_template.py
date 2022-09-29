from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    no_commission = fields.Boolean('Exclude from Commissions')
    can_edit_no_commission = fields.Boolean(compute='_compute_can_edit_no_commission')

    def _compute_can_edit_no_commission(self):
        can_edit = self.env.user.has_group('account.group_account_user')
        for template in self:
            template.can_edit_no_commission = can_edit
