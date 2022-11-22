from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.queue_job.exception import NothingToDoJob, RetryableJobError
from odoo.addons.component.core import Component


class OpencartProductTemplate(models.Model):
    _name = 'opencart.product.template'
    _inherit = 'opencart.binding'
    _inherits = {'product.template': 'odoo_id'}
    _description = 'Opencart Product'

    odoo_id = fields.Many2one('product.template',
                              string='Product',
                              required=True,
                              ondelete='cascade')  # cascade so that you can delete an Odoo product that was created by connector
    opencart_attribute_value_ids = fields.One2many('opencart.product.template.attribute.value',
                                                   'opencart_product_tmpl_id',
                                                   string='Opencart Product Attribute Values')

    def opencart_sale_line_custom_value_commands(self, options):
        """Receives 'custom options' and returns commands for SO lines to link to.
        This method will setup the product template to support the supplied commands."""
        commands = []
        for option in options:
            c_attr_name = option.get('name')
            c_attr_value = option.get('value')
            if not all((c_attr_name, c_attr_value)):
                raise UserError('Mapping sale order custom values cannot happen if the option is missing name or value. Original option payload: ' + str(option))
            # note this is a weak binding because the name could change, even due to translation
            attr_line = self.odoo_id.attribute_line_ids.filtered(lambda l: l.attribute_id.name == c_attr_name)
            if not attr_line:
                attribute = self.env['product.attribute'].search([('name', '=', c_attr_name)], limit=1)
                if not attribute:
                    # we will have to assume some things about the attribute
                    attribute = self.env['product.attribute'].create({
                        'name': c_attr_name,
                        'create_variant': 'no_variant',
                        # 'visibility': 'hidden',  # TODO who adds this field
                        'value_ids': [(0, 0, {
                            'attribute_id': attribute.id,
                            'name': 'opencart-custom',  # people can rename it.
                            'is_custom': True,
                        })],
                    })
                value = attribute.value_ids.filtered('is_custom')
                if len(value) > 1:
                    value = value[0]
                # while we may not have a value here, the exception should tell us as much as us raising one ourself
                # now we have an attribute, we can make an attribute value line with one custom va
                self.odoo_id.write({
                    'attribute_line_ids': [(0, 0, {
                        'attribute_id': attribute.id,
                        'value_ids': [(4, value.id)]
                    })]
                })
                attr_line = self.odoo_id.attribute_line_ids.filtered(lambda l: l.attribute_id == attribute)
            # now we have a product template attribute line, it should have a custom value
            attr_line_value = attr_line.product_template_value_ids.filtered(lambda v: v.is_custom)
            if len(attr_line_value) > 1:
                attr_line_value = attr_line_value[0]
            # again we may not have a value, but the exception will be on the SOL side
            commands.append((0, 0, {
                'custom_product_template_attribute_value_id': attr_line_value.id,
                'custom_value': c_attr_value,
            }))
        return commands

    def opencart_sale_get_combination(self, options, reentry=False):
        # note we EXPECT every option passed in here to have a 'product_option_value_id'
        # filtering them out at this step is not desirable because of the recursive entry with options
        if not options:
            return self.odoo_id.product_variant_id
        selected_attribute_values = self.env['product.template.attribute.value']
        for option in options:
            product_option_value_id = str(option['product_option_value_id'])
            opencart_attribute_value = self.opencart_attribute_value_ids.filtered(lambda v: v.external_id == product_option_value_id)
            if not opencart_attribute_value:
                if reentry:
                    # we have already triggered an import.
                    raise Exception('Order Product has option (%s) "%s" that does not exist on the product.' % (product_option_value_id, option.get('name', '<Empty>')))
                # need to re-import product.
                try:
                    self.import_record(self.backend_id, self.external_id, force=True)
                    return self.opencart_sale_get_combination(options, reentry=True)
                except NothingToDoJob:
                    if reentry:
                        raise RetryableJobError('Product imported, but selected option is not available.')
            if not opencart_attribute_value.odoo_id:
                raise RetryableJobError('Order Product (%s) has option (%s) "%s" that is not mapped to an Odoo Attribute Value.' % (self, opencart_attribute_value.external_id, opencart_attribute_value.opencart_name))
            selected_attribute_values |= opencart_attribute_value.odoo_id
        # we always need to 'select' template attr values for 'no variant' options
        # this is only need if it creates the variant because this value cannot be skipped otherwise it is an invalid variant
        for line in self.odoo_id.attribute_line_ids.filtered(lambda pal: pal.attribute_id.create_variant == 'no_variant'):
            # and there must always bee at least one
            selected_attribute_values |= line.product_template_value_ids[0]
        # Now that we know what options are selected, we can load a variant with those options
        product = self.odoo_id._create_product_variant(selected_attribute_values, log_warning=True)
        if not product:
            raise Exception('No product can be created for selected attribute values, check logs. ' + str(selected_attribute_values))
        return product


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    opencart_sku = fields.Char('Opencart SKU')
    opencart_bind_ids = fields.One2many('opencart.product.template', 'odoo_id', string='Opencart Bindings')


class OpencartProductTemplateAdapter(Component):
    _name = 'opencart.product.template.adapter'
    _inherit = 'opencart.adapter'
    _apply_on = 'opencart.product.template'

    def read(self, id):
        api_instance = self.api_instance
        record = api_instance.products.get(id)
        if 'data' in record and record['data']:
            return record['data']
        raise RetryableJobError('Product "' + str(id) + '" did not return an product response. ' + str(record))


# Product Attribute Value, cannot "inherits" the odoo_id as then it cannot be empty
class OpencartProductTemplateAttributeValue(models.Model):
    _name = 'opencart.product.template.attribute.value'
    _inherit = 'opencart.binding'
    _description = 'Opencart Product Attribute Value'

    odoo_id = fields.Many2one('product.template.attribute.value',
                              string='Product Attribute Value',
                              required=False,
                              ondelete='cascade')
    opencart_name = fields.Char(string='Opencart Name', help='For matching purposes.')
    opencart_product_tmpl_id = fields.Many2one('opencart.product.template',
                                               string='Opencart Product',
                                               required=True,
                                               ondelete='cascade')
    product_tmpl_id = fields.Many2one(related='opencart_product_tmpl_id.odoo_id')

    # The regular constraint won't work here because multiple templates can/will have the same attribute id in opencart
    _sql_constraints = [
        ('opencart_uniq', 'unique(backend_id, external_id, opencart_product_tmpl_id)', 'A binding already exists for this Opencart ID+Product Template.'),
    ]
