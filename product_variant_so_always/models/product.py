from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    always_variant_on_so = fields.Boolean(string='Always create variants on SO Lines')

    def has_dynamic_attributes(self):
        self.ensure_one()
        if self.always_variant_on_so:
            return True
        return super(ProductTemplate, self).has_dynamic_attributes()
