from odoo import api, fields, models, _


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

    """
    This override will move 'default' attribute values to the top of the possible combinations to allow
    reasonable amount of time to get '_get_first_possible_combination' on a VERY large product configuration.
    """
    @api.multi
    def _get_possible_combinations(self, parent_combination=None, necessary_values=None):
        """Generator returning combinations that are possible, following the
        sequence of attributes and values.

        See `_is_combination_possible` for what is a possible combination.

        When encountering an impossible combination, try to change the value
        of attributes by starting with the further regarding their sequences.

        Ignore attributes that have no values.

        :param parent_combination: combination from which `self` is an
            optional or accessory product.
        :type parent_combination: recordset `product.template.attribute.value`

        :param necessary_values: values that must be in the returned combination
        :type necessary_values: recordset of `product.template.attribute.value`

        :return: the possible combinations
        :rtype: generator of recordset of `product.template.attribute.value`
        """
        self.ensure_one()

        if not self.active:
            return _("The product template is archived so no combination is possible.")

        necessary_values = necessary_values or self.env['product.template.attribute.value']
        necessary_attributes = necessary_values.mapped('attribute_id')
        ptal_stack = [self.valid_product_template_attribute_line_ids.filtered(lambda ptal: ptal.attribute_id not in necessary_attributes)]
        combination_stack = [necessary_values]

        # keep going while we have attribute lines to test
        while len(ptal_stack):
            attribute_lines = ptal_stack.pop()
            combination = combination_stack.pop()

            if not attribute_lines:
                # full combination, if it's possible return it, otherwise skip it
                if self._is_combination_possible(combination, parent_combination):
                    yield(combination)
            else:
                # we have remaining attribute lines to consider
                for ptav in reversed(attribute_lines[0].product_template_value_ids.sorted(lambda l: not l.is_default)):
                    ptal_stack.append(attribute_lines[1:])
                    combination_stack.append(combination + ptav)

        return _("There are no remaining possible combination.")

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    is_default = fields.Boolean(string='Use as Default', copy=False)
