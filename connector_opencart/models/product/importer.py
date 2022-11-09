from html import unescape
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ProductImportMapper(Component):
    _name = 'opencart.product.template.import.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = ['opencart.product.template']

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def name(self, record):
        name = record.get('product_description', [{}])[0].get('name', record.get('id'))
        return {'name': unescape(name)}

    @only_create
    @mapping
    def product_type(self, record):
        # why this check if @only_create?
        # well because we would turn the binding create into a very real product.template.write
        existing_product = self.existing_product(record)
        if existing_product and existing_product.get('odoo_id'):
            return {'type': self.env['product.template'].browse(existing_product['odoo_id']).type}
        return {'type': 'product' if record.get('shipping') else 'service'}

    @mapping
    def opencart_sku(self, record):
        sku = str(record.get('model') or record.get('sku') or '').strip()
        return {'opencart_sku': sku}

    @only_create
    @mapping
    def existing_product(self, record):
        product_template = self.env['product.template']
        template = product_template.browse()

        if record.get('model'):
            model = str(record.get('model') or '').strip()
            # Try to match our own field
            template = product_template.search([('opencart_sku', '=', model)], limit=1)
            if not template:
                # Try to match the default_code
                template = product_template.search([('default_code', '=', model)], limit=1)
        if not template and record.get('sku'):
            sku = str(record.get('sku') or '').strip()
            template = product_template.search([('opencart_sku', '=', sku)], limit=1)
            if not template:
                template = product_template.search([('default_code', '=', sku)], limit=1)
        if not template and record.get('name'):
            name = record.get('product_description', [{}])[0].get('name')
            if name:
                template = product_template.search([('name', '=', unescape(name))], limit=1)
        return {'odoo_id': template.id}
    
    @mapping
    def checkpoint_summary(self, record):
        pieces = [
            str(record.get('model') or '').strip(),
            str(record.get('sku') or '').strip(),
            str(record.get('product_description', [{}])[0].get('name') or '').strip(),
        ]
        pieces = [t for t in pieces if t]
        return {'checkpoint_summary': ' : '.join(pieces)}


class ProductImporter(Component):
    _name = 'opencart.product.template.importer'
    _inherit = 'opencart.importer'
    _apply_on = ['opencart.product.template']

    def _create(self, data):
        checkpoint_summary = data.get('checkpoint_summary', '')
        if 'checkpoint_summary' in data:
            del data['checkpoint_summary']
        binding = super(ProductImporter, self)._create(data)
        self.backend_record.add_checkpoint(binding, summary=checkpoint_summary)
        return binding

    def _after_import(self, binding):
        self._sync_options(binding)

    def _sync_options(self, binding):
        existing_option_values = binding.opencart_attribute_value_ids
        mapped_option_values = binding.opencart_attribute_value_ids.browse()
        record = self.opencart_record
        backend = self.backend_record
        for option in record.get('options', []):
            for record_option_value in option.get('option_value', []):
                option_value = existing_option_values.filtered(lambda v: v.external_id == str(record_option_value['product_option_value_id']))
                name = unescape(record_option_value.get('name', ''))
                if not option_value:
                    option_value = existing_option_values.create({
                        'backend_id': backend.id,
                        'external_id': record_option_value['product_option_value_id'],
                        'opencart_name': name,
                        'opencart_product_tmpl_id': binding.id,
                    })
                # Keep options consistent with Opencart by renaming them
                if option_value.opencart_name != name:
                    option_value.opencart_name = name
                mapped_option_values += option_value

        to_unlink = existing_option_values - mapped_option_values
        to_unlink.unlink()
