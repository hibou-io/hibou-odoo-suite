from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_default_attribute_values(self, so_line):
        product = None
        if so_line:
            product = so_line.product_id
        attribute_values = self.env['product.attribute.value'].browse()
        for attribute_line in self.attribute_line_ids:
            attribute = attribute_line.attribute_id
            attribute_line_values = attribute_line.product_template_value_ids

            # Product Values
            if product:
                product_values = product.attribute_value_ids.filtered(lambda v: v.attribute_id == attribute)
                if product_values:
                    attribute_values += product_values
                    continue

                so_line_values = so_line.product_no_variant_attribute_value_ids.filtered(
                    lambda v: v.attribute_id == attribute)
                if so_line_values:
                    attribute_values += so_line_values.mapped('product_attribute_value_id')
                    continue

            default_value = self.env['product.template.attribute.value'].search([
                ('product_tmpl_id', '=', self.id),
                ('attribute_id', '=', attribute.id),
                ('is_default', '=', True),
            ], limit=1)
            if default_value:
                attribute_values += default_value.mapped('product_attribute_value_id')
                continue

            # First value
            attribute_values += attribute_line_values[0].product_attribute_value_id

        return attribute_values


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    is_default = fields.Boolean(string='Use as Default', copy=False)
