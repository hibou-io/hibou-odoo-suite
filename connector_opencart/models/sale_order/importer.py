# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime, timedelta
from copy import deepcopy, copy

from odoo import fields, _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    _name = 'opencart.sale.order.batch.importer'
    _inherit = 'opencart.delayed.batch.importer'
    _apply_on = 'opencart.sale.order'

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
        external_ids = list(self.backend_adapter.search(filters))
        for external_id in external_ids:
            self._import_record(external_id)
        if external_ids:
            last_id = list(sorted(external_ids))[-1]
            self.backend_record.import_orders_after_id = last_id


class SaleOrderImportMapper(Component):


    _name = 'opencart.sale.order.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = 'opencart.sale.order'

    direct = [('order_id', 'external_id'),
              # ('customerOrderId', 'customer_order_id'),
              ]

    children = [('products', 'opencart_order_line_ids', 'opencart.sale.order.line'),
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
        # will I need more?!
        return onchange.play(values, values['opencart_order_line_ids'])

    @mapping
    def name(self, record):
        name = str(record['order_id'])
        prefix = self.backend_record.sale_prefix
        if prefix:
            name = prefix + name
        return {'name': name}

    @mapping
    def date_order(self, record):
        return {'date_order': record.get('date_added', fields.Datetime.now())}

    @mapping
    def fiscal_position_id(self, record):
        if self.backend_record.fiscal_position_id:
            return {'fiscal_position_id': self.backend_record.fiscal_position_id.id}

    @mapping
    def team_id(self, record):
        if self.backend_record.team_id:
            return {'team_id': self.backend_record.team_id.id}

    @mapping
    def payment_mode_id(self, record):
        record_method = record['payment_method']
        method = self.env['account.payment.mode'].search(
            [('name', '=', record_method)],
            limit=1,
        )
        assert method, ("method %s should exist because the import fails "
                        "in SaleOrderImporter._before_import when it is "
                        " missing" % record_method)
        return {'payment_mode_id': method.id}

    @mapping
    def project_id(self, record):
        if self.backend_record.analytic_account_id:
            return {'project_id': self.backend_record.analytic_account_id.id}

    @mapping
    def warehouse_id(self, record):
        if self.backend_record.warehouse_id:
            return {'warehouse_id': self.backend_record.warehouse_id.id}

    @mapping
    def shipping_method(self, record):
        method = record['shipping_method']
        carrier = self.env['delivery.carrier'].search([('opencart_code', '=', method)], limit=1)
        if not carrier:
            raise ValueError('Delivery Carrier for methodCode "%s", cannot be found.' % (method, ))
        return {'carrier_id': carrier.id, 'shipping_method_code': method}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def total_amount(self, record):
        # lines = record['total']
        total_amount = record['total']
        total_amount_tax = 0.0
        # for l in lines:
        #     item_amount, tax_amount = walk_charges(l['charges'])
        #     total_amount += item_amount + tax_amount
        #     total_amount_tax += tax_amount
        return {'total_amount': total_amount, 'total_amount_tax': total_amount_tax}


class SaleOrderImporter(Component):
    _name = 'opencart.sale.order.importer'
    _inherit = 'opencart.importer'
    _apply_on = 'opencart.sale.order'

    def _must_skip(self):
        if self.binder.to_internal(self.external_id):
            return _('Already imported')

    def _before_import(self):
        # Check if status is ok, etc. on self.opencart_record
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

    def _make_partner_name(self, firstname, lastname):
        name = (str(firstname) + ' ' + str(lastname)).strip()
        if not name:
            return 'Undefined'
        return name

    def _get_partner_values(self, info_string='shipping_'):
        record = self.opencart_record

        # find or make partner with these details.
        email = record.get('email')
        if not email:
            raise ValueError('Order does not have email in : ' + str(record))

        phone = record.get('telephone', False)

        info = {}
        for k, v in record.items():
            # Strip the info_string so that the remainder of the code depends on it.
            if k.find(info_string) == 0:
                info[k[len(info_string):]] = v


        name = self._make_partner_name(info.get('firstname', ''), info.get('lastname', ''))
        street = info.get('address_1', '')
        street2 = info.get('address_2', '')
        city = info.get('city', '')
        state_code = info.get('zone_code', '')
        zip_ = info.get('postcode', '')
        country_code = info.get('iso_code_2', '')
        country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id),
            ('code', '=', state_code)
        ], limit=1)

        return {
            'email': email,
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
        record = self.opencart_record

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

        invoice_values = self._get_partner_values(info_string='payment_')

        if (not self._partner_matches(partner, invoice_values)
                and not self._partner_matches(shipping_partner, invoice_values)):
            partner_values['parent_id'] = partner.id
            partner_values['active'] = False
            invoice_partner = self._create_partner(copy(invoice_values))
        elif self._partner_matches(partner, invoice_values):
            invoice_partner = partner
        elif self._partner_matches(shipping_partner, invoice_values):
            invoice_partner = shipping_partner

        self.partner = partner
        self.shipping_partner = shipping_partner
        self.invoice_partner = invoice_partner

    def _check_special_fields(self):
        assert self.partner, (
            "self.partner should have been defined "
            "in SaleOrderImporter._import_addresses")
        assert self.shipping_partner, (
            "self.shipping_partner should have been defined "
            "in SaleOrderImporter._import_addresses")
        assert self.invoice_partner, (
            "self.invoice_partner should have been defined "
            "in SaleOrderImporter._import_addresses")

    def _create_data(self, map_record, **kwargs):
        # non dependencies
        self._check_special_fields()
        return super(SaleOrderImporter, self)._create_data(
            map_record,
            partner_id=self.partner.id,
            partner_invoice_id=self.invoice_partner.id,
            partner_shipping_id=self.shipping_partner.id,
            **kwargs
        )

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        # Without this, it won't map taxes with the fiscal position.
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()

        # if binding.backend_id.acknowledge_order == 'order_create':
        #     binding.with_delay().acknowledge_order(binding.backend_id, binding.external_id)

        return binding

    def _import_dependencies(self):
        record = self.opencart_record

        self._import_addresses()

class SaleOrderLineImportMapper(Component):

    _name = 'opencart.sale.order.line.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = 'opencart.sale.order.line'

    direct = [('quantity', 'product_uom_qty'),
              ('price', 'price_unit'),
              ('name', 'name'),
              ('order_product_id', 'external_id'),
              ]

    def _finalize_product_values(self, record, values):
        # This would be a good place to create a vendor or add a route...
        return values

    def _product_values(self, record):
        reference = record['model']
        values = {
            'default_code': reference,
            'name': record.get('name', reference),
            'type': 'product',
            'list_price': record.get('price', 0.0),
            'categ_id': self.backend_record.product_categ_id.id,
        }
        return self._finalize_product_values(record, values)

    @mapping
    def product_id(self, record):
        reference = record['model']
        product = self.env['product.product'].search([
            ('default_code', '=', reference)
        ], limit=1)

        if not product:
            # we could use a record like (0, 0, values)
            product = self.env['product.product'].create(self._product_values(record))

        return {'product_id': product.id}
