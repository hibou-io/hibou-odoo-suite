# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime, timedelta
from copy import deepcopy, copy

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError

_logger = logging.getLogger(__name__)


def walk_charges(charges):
    item_amount = 0.0
    tax_amount = 0.0
    for charge in charges['charge']:
        #charge_details = charge['charge']
        charge_details = charge
        charge_amount_details = charge_details['chargeAmount']
        assert charge_amount_details['currency'] == 'USD', ("Invalid currency: " + charge_amount_details['currency'])
        tax_details = charge_details['tax']
        tax_amount_details = tax_details['taxAmount'] if tax_details else {'amount': 0.0}
        item_amount += float(charge_amount_details['amount'])
        tax_amount += float(tax_amount_details['amount'])
    return item_amount, tax_amount


class SaleOrderBatchImporter(Component):
    _name = 'walmart.sale.order.batch.importer'
    _inherit = 'walmart.delayed.batch.importer'
    _apply_on = 'walmart.sale.order'

    def _import_record(self, external_id, job_options=None, **kwargs):
        if not job_options:
            job_options = {
                'max_retries': 0,
                'priority': 5,
            }
        return super(SaleOrderBatchImporter, self)._import_record(
            external_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        from_date = filters.get('from_date')
        next_cursor = filters.get('next_cursor')
        external_ids = self.backend_adapter.search(
            from_date=from_date,
            next_cursor=next_cursor,
        )
        for external_id in external_ids:
            self._import_record(external_id)



class SaleOrderImportMapper(Component):

    _name = 'walmart.sale.order.mapper'
    _inherit = 'walmart.import.mapper'
    _apply_on = 'walmart.sale.order'

    direct = [('purchaseOrderId', 'external_id'),
              ('customerOrderId', 'customer_order_id'),
              ]

    children = [('orderLines', 'walmart_order_line_ids', 'walmart.sale.order.line'),
                ]

    # def _map_child(self, map_record, from_attr, to_attr, model_name):
    #     return super(SaleOrderImportMapper, self)._map_child(map_record, from_attr, to_attr, model_name)

    def _add_shipping_line(self, map_record, values):
        record = map_record.source

        line_builder = self.component(usage='order.line.builder.shipping')
        line_builder.price_unit = 0.0

        if values.get('carrier_id'):
            carrier = self.env['delivery.carrier'].browse(values['carrier_id'])
            line_builder.product = carrier.product_id

        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def finalize(self, map_record, values):
        values.setdefault('order_line', [])
        self._add_shipping_line(map_record, values)
        values.update({
            'partner_id': self.options.partner_id,
            'partner_invoice_id': self.options.partner_invoice_id,
            'partner_shipping_id': self.options.partner_shipping_id,
        })
        onchange = self.component(
            usage='ecommerce.onchange.manager.sale.order'
        )
        return onchange.play(values, values['walmart_order_line_ids'])

    @mapping
    def name(self, record):
        name = record['purchaseOrderId']
        prefix = self.backend_record.sale_prefix
        if prefix:
            name = prefix + name
        return {'name': name}

    @mapping
    def date_order(self, record):
        return {'date_order': datetime.fromtimestamp(record['orderDate'] / 1e3)}

    @mapping
    def fiscal_position_id(self, record):
        if self.backend_record.fiscal_position_id:
            return {'fiscal_position_id': self.backend_record.fiscal_position_id.id}

    @mapping
    def team_id(self, record):
        if self.backend_record.team_id:
            return {'team_id': self.backend_record.team_id.id}

    @mapping
    def user_id(self, record):
        if self.backend_record.user_id:
            return {'user_id': self.backend_record.user_id.id}

    @mapping
    def payment_mode_id(self, record):
        assert self.backend_record.payment_mode_id, ("Payment mode must be specified.")
        return {'payment_mode_id': self.backend_record.payment_mode_id.id}

    @mapping
    def analytic_account_id(self, record):
        if self.backend_record.analytic_account_id:
            return {'analytic_account_id': self.backend_record.analytic_account_id.id}

    @mapping
    def warehouse_id(self, record):
        if self.backend_record.warehouse_id:
            return {'warehouse_id': self.backend_record.warehouse_id.id}

    @mapping
    def shipping_method(self, record):
        method = record['shippingInfo']['methodCode']
        carrier = self.env['delivery.carrier'].search([('walmart_code', '=', method)], limit=1)
        if not carrier:
            raise ValueError('Delivery Carrier for methodCode "%s", cannot be found.' % (method, ))
        return {'carrier_id': carrier.id, 'shipping_method_code': method}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def total_amount(self, record):
        lines = record['orderLines']
        total_amount = 0.0
        total_amount_tax = 0.0
        for l in lines:
            item_amount, tax_amount = walk_charges(l['charges'])
            total_amount += item_amount + tax_amount
            total_amount_tax += tax_amount
        return {'total_amount': total_amount, 'total_amount_tax': total_amount_tax}


class SaleOrderImporter(Component):
    _name = 'walmart.sale.order.importer'
    _inherit = 'walmart.importer'
    _apply_on = 'walmart.sale.order'

    def _must_skip(self):
        if self.binder.to_internal(self.external_id):
            return _('Already imported')

    def _before_import(self):
        # @TODO check if the order is released
        pass

    def _create_partner(self, values):
        return self.env['res.partner'].create(values)

    def _partner_matches(self, partner, values):
        for key, value in values.items():
            if key == 'state_id':
                if value != partner.state_id.id:
                    return False
            elif key == 'country_id':
                if value != partner.country_id.id:
                    return False
            elif bool(value) and value != getattr(partner, key):
                return False
        return True

    def _get_partner_values(self):
        record = self.walmart_record

        # find or make partner with these details.
        if 'customerEmailId' not in record:
            raise ValueError('Order does not have customerEmailId in : ' + str(record))
        customer_email = record['customerEmailId']
        shipping_info = record['shippingInfo']
        phone = shipping_info.get('phone', '')
        postal_address = shipping_info.get('postalAddress', [])
        name = postal_address.get('name', 'Undefined')
        street = postal_address.get('address1', '')
        street2 = postal_address.get('address2', '')
        city = postal_address.get('city', '')
        state_code = postal_address.get('state', '')
        zip_ = postal_address.get('postalCode', '')
        country_code = postal_address['country']
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id),
            ('code', '=', state_code)
        ], limit=1)

        return {
            'email': customer_email,
            'name': name,
            'phone': phone,
            'street': street,
            'street2': street2,
            'zip': zip_,
            'city': city,
            'state_id': state.id,
            'country_id': country.id,
        }


    def _import_addresses(self):
        record = self.walmart_record

        partner_values = self._get_partner_values()
        partner = self.env['res.partner'].search([
            ('email', '=', partner_values['email']),
        ], limit=1)

        if not partner:
            # create partner.
            partner = self._create_partner(copy(partner_values))

        if not self._partner_matches(partner, partner_values):
            partner_values['parent_id'] = partner.id
            partner_values['active'] = False
            shipping_partner = self._create_partner(copy(partner_values))
        else:
            shipping_partner = partner

        self.partner = partner
        self.shipping_partner = shipping_partner

    def _check_special_fields(self):
        assert self.partner, (
            "self.partner should have been defined "
            "in SaleOrderImporter._import_addresses")
        assert self.shipping_partner, (
            "self.shipping_partner should have been defined "
            "in SaleOrderImporter._import_addresses")

    def _create_data(self, map_record, **kwargs):
        # non dependencies
        self._check_special_fields()
        return super(SaleOrderImporter, self)._create_data(
            map_record,
            partner_id=self.partner.id,
            partner_invoice_id=self.shipping_partner.id,
            partner_shipping_id=self.shipping_partner.id,
            **kwargs
        )

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        # Without this, it won't map taxes with the fiscal position.
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()

        if binding.backend_id.acknowledge_order == 'order_create':
            binding.with_delay().acknowledge_order(binding.backend_id, binding.external_id)

        return binding


    def _import_dependencies(self):
        record = self.walmart_record

        self._import_addresses()

        # @TODO Import lines?
        # Actually, maybe not, since I'm just going to reference by sku



class SaleOrderLineImportMapper(Component):

    _name = 'walmart.sale.order.line.mapper'
    _inherit = 'walmart.import.mapper'
    _apply_on = 'walmart.sale.order.line'

    def _finalize_product_values(self, record, values):
        # This would be a good place to create a vendor or add a route...
        return values

    def _product_values(self, record):
        item = record['item']
        sku = item['sku']
        item_amount, _ = walk_charges(record['charges'])
        values = {
            'default_code': sku,
            'name': item.get('productName', sku),
            'type': 'product',
            'list_price': item_amount,
            'categ_id': self.backend_record.product_categ_id.id,
        }
        return self._finalize_product_values(record, values)

    @mapping
    def product_id(self, record):
        item = record['item']
        sku = item['sku']
        product = self.env['product.template'].search([
            ('default_code', '=', sku)
        ], limit=1)

        if not product:
            # we could use a record like (0, 0, values)
            product = self.env['product.template'].create(self._product_values(record))

        return {'product_id': product.product_variant_id.id}

    @mapping
    def price_unit(self, record):
        order_line_qty = record['orderLineQuantity']
        product_uom_qty = int(order_line_qty['amount'])
        item_amount, tax_amount = walk_charges(record['charges'])
        tax_rate = (tax_amount / item_amount) * 100.0 if item_amount else 0.0

        price_unit = item_amount / product_uom_qty

        return {'product_uom_qty': product_uom_qty, 'price_unit': price_unit, 'tax_rate': tax_rate}

    @mapping
    def walmart_number(self, record):
        return {'walmart_number': record['lineNumber']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

