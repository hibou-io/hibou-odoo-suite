# © 2021 Hibou Corp.

import logging
from json import dumps

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import RetryableJobError, NothingToDoJob
from ...components.mapper import normalize_datetime
from ..api import make_amz_pii_cipher, make_amz_pii_encrypt

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    _name = 'amazon.sale.order.batch.importer'
    _inherit = 'amazon.delayed.batch.importer'
    _apply_on = 'amazon.sale.order'

    def _import_record(self, external_id, job_options=None, **kwargs):
        if not job_options:
            job_options = {
                'max_retries': 0,
                'priority': 30,
            }
        return super(SaleOrderBatchImporter, self)._import_record(
            external_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        res = self.backend_adapter.search(filters)
        orders = res.get('Orders', [])
        for order in orders:
            self._import_record(order['AmazonOrderId'])


class SaleOrderImportMapper(Component):
    _name = 'amazon.sale.order.mapper'
    _inherit = 'amazon.import.mapper'
    _apply_on = 'amazon.sale.order'

    direct = [
        ('AmazonOrderId', 'external_id'),
        (normalize_datetime('PurchaseDate'), 'effective_date'),
        (normalize_datetime('LatestShipDate'), 'date_planned'),
        (normalize_datetime('LatestDeliveryDate'), 'requested_date'),
        ('ShipServiceLevel', 'ship_service_level'),
        ('ShipmentServiceLevelCategory', 'ship_service_level_category'),
        ('MarketplaceId', 'marketplace'),
        ('OrderType', 'order_type'),
        ('IsBusinessOrder', 'is_business_order'),
        ('IsPrime', 'is_prime'),
        ('IsGlobalExpressEnabled', 'is_global_express_enabled'),
        ('IsPremiumOrder', 'is_premium'),
        ('IsSoldByAB', 'is_sold_by_ab'),
        ('FulfillmentChannel', 'fulfillment_channel'),
    ]

    children = [
        ('OrderItems', 'amazon_order_line_ids', 'amazon.sale.order.line'),
    ]

    def _add_shipping_line(self, map_record, values):
        # Any reason it wouldn't always be free?
        # We need a delivery line to prevent shipping from invoicing cost of shipping.
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
        return onchange.play(values, values['amazon_order_line_ids'])

    def is_fba(self, record):
        return record.get('FulfillmentChannel') == 'AFN'

    @mapping
    def name(self, record):
        name = record['AmazonOrderId']
        prefix = self.backend_record.fba_sale_prefix if self.is_fba(record) else self.backend_record.sale_prefix
        if prefix:
            name = prefix + name
        return {'name': name}

    @mapping
    def total_amount(self, record):
        return {'total_amount': float(record.get('OrderTotal', {}).get('Amount', '0.0'))}

    @mapping
    def currency_id(self, record):
        currency_code = record.get('OrderTotal', {}).get('CurrencyCode')
        if not currency_code:
            # TODO default to company currency if not specified
            return {}
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        return {'currency_id': currency.id}

    @mapping
    def warehouse_id(self, record):
        warehouses = self.backend_record.warehouse_ids + self.backend_record.fba_warehouse_ids
        postal_code = record.get('DefaultShipFromLocationAddress', {}).get('PostalCode')
        if not warehouses or not postal_code:
            # use default
            warehouses = self.backend_record.fba_warehouse_ids if self.is_fba(record) else self.backend_record.warehouse_ids
            for warehouse in warehouses:
                # essentially the first of either regular or FBA warehouses
                return {'warehouse_id': warehouse.id, 'company_id': warehouse.company_id.id}
            return {}
        warehouses = warehouses.filtered(lambda w: w.partner_id.zip == postal_code)
        for warehouse in warehouses:
            return {'warehouse_id': warehouse.id, 'company_id': warehouse.company_id.id}
        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def fiscal_position_id(self, record):
        fiscal_position = self.backend_record.fba_fiscal_position_id if self.is_fba(record) else self.backend_record.fiscal_position_id
        if fiscal_position:
            return {'fiscal_position_id': fiscal_position.id}

    @mapping
    def team_id(self, record):
        team = self.backend_record.fba_team_id if self.is_fba(record) else self.backend_record.team_id
        if team:
            return {'team_id': team.id}

    @mapping
    def user_id(self, record):
        user = self.backend_record.fba_user_id if self.is_fba(record) else self.backend_record.user_id
        if user:
            return {'user_id': user.id}

    @mapping
    def payment_mode_id(self, record):
        payment_mode = self.backend_record.fba_payment_mode_id if self.is_fba(record) else self.backend_record.payment_mode_id
        assert payment_mode, ("Payment mode must be specified on the Amazon Backend.")
        return {'payment_mode_id': payment_mode.id}

    @mapping
    def analytic_account_id(self, record):
        analytic_account = self.backend_record.fba_analytic_account_id if self.is_fba(record) else self.backend_record.analytic_account_id
        if analytic_account:
            return {'analytic_account_id': analytic_account.id}

    @mapping
    def carrier_id(self, record):
        carrier = self.backend_record.fba_carrier_id if self.is_fba(record) else self.backend_record.carrier_id
        if carrier:
            return {'carrier_id': carrier.id}


class SaleOrderImporter(Component):
    _name = 'amazon.sale.order.importer'
    _inherit = 'amazon.importer'
    _apply_on = 'amazon.sale.order'

    def _get_amazon_data(self):
        """ Return the raw Amazon data for ``self.external_id`` """
        return self.backend_adapter.read(self.external_id,
                                         include_order_items=True,
                                         include_order_address=True,
                                         include_order_buyer_info=True,
                                         include_order_items_buyer_info=False,  # this call doesn't add anything useful
                                         )

    def _must_skip(self):
        if self.binder.to_internal(self.external_id):
            return _('Already imported')

    def _before_import(self):
        status = self.amazon_record.get('OrderStatus')
        if status == 'Pending':
            raise RetryableJobError('Order is Pending')
        if status == 'Canceled':
            raise NothingToDoJob('Order is Cancelled')

    def _create_partner(self, values):
        return self.env['res.partner'].create(values)

    def _get_partner_values(self):
        cipher = make_amz_pii_cipher(self.env)
        if cipher:
            amz_pii_encrypt = make_amz_pii_encrypt(cipher)
        else:
            def amz_pii_encrypt(value):
                return value
        
        record = self.amazon_record

        # find or make partner with these details.
        if 'OrderAddress' not in record or 'ShippingAddress' not in record['OrderAddress']:
            raise ValueError('Order does not have OrderAddress.ShippingAddress in : ' + str(record))
        ship_info = record['OrderAddress']['ShippingAddress']

        email = record.get('OrderBuyerInfo', {}).get('BuyerEmail', '')
        phone = ship_info.get('Phone') or ''
        if phone:
            phone = amz_pii_encrypt(phone)
        name = ship_info.get('Name')
        if name:
            name = amz_pii_encrypt(name)
        else:
            name = record['AmazonOrderId']  # customer will be named after order....

        street = ship_info.get('AddressLine1') or ''
        if street:
            street = amz_pii_encrypt(street)
        street2 = ship_info.get('AddressLine2') or ''
        if street2:
            street2 = amz_pii_encrypt(street2)
        city = ship_info.get('City') or ''
        country_code = ship_info.get('CountryCode') or ''
        country_id = False
        if country_code:
            country_id = self.env['res.country'].search([('code', '=ilike', country_code)], limit=1).id
        state_id = False
        state_code = ship_info.get('StateOrRegion') or ''
        if state_code:
            state_domain = [('code', '=ilike', state_code)]
            if country_id:
                state_domain.append(('country_id', '=', country_id))
            state_id = self.env['res.country.state'].search(state_domain, limit=1).id
        if not state_id and state_code:
            # Amazon can send some strange stuff like 'TEXAS'
            state_domain[0] = ('name', '=ilike', state_code)
            state_id = self.env['res.country.state'].search(state_domain, limit=1).id
        zip_ = ship_info.get('PostalCode') or ''
        res = {
            'email': email,
            'name': name,
            'phone': phone,
            'street': street,
            'street2': street2,
            'zip': zip_,
            'city': city,
            'state_id': state_id,
            'country_id': country_id,
            'type': 'contact',
        }
        _logger.warn('partner values: ' + str(res))
        return res

    def _import_addresses(self):
        partner_values = self._get_partner_values()
        # Find or create a 'parent' partner for the address.
        if partner_values['email']:
            partner = self.env['res.partner'].search([
                ('email', '=', partner_values['email']),
                ('parent_id', '=', False)
            ], limit=1)
        else:
            partner = self.env['res.partner'].search([
                ('name', '=', partner_values['name']),
                ('parent_id', '=', False)
            ], limit=1)
        if not partner:
            # create partner.
            partner = self._create_partner({'name': partner_values['name'], 'email': partner_values['email']})

        partner_values['parent_id'] = partner.id
        partner_values['type'] = 'other'
        shipping_partner = self._create_partner(partner_values)

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

    def _create_plan(self, binding):
        plan = None
        if not binding.is_fba():
            # I really do not like that we need to use planner here.
            # it adds to the setup and relies on the planner being setup with the appropriate warehouses.
            # Why Amazon, can you not just tell me which warehouse?
            options = self.env['sale.order.make.plan'].generate_order_options(binding.odoo_id, plan_shipping=False)
            if options:
                plan = options[0]

                sub_options = plan.get('sub_options')
                # serialize lines
                if sub_options:
                    plan['sub_options'] = dumps(sub_options)
        if plan:
            option = self.env['sale.order.planning.option'].create(plan)
            self.env['sale.order.make.plan'].plan_order_option(binding.odoo_id, option)

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        self._create_plan(binding)
        # Without this, it won't map taxes with the fiscal position.
        if binding.fiscal_position_id:
            binding.odoo_id._compute_tax_id()

        return binding

    def _import_dependencies(self):
        record = self.amazon_record

        self._import_addresses()


class SaleOrderLineImportMapper(Component):

    _name = 'amazon.sale.order.line.mapper'
    _inherit = 'amazon.import.mapper'
    _apply_on = 'amazon.sale.order.line'

    direct = [
        ('OrderItemId', 'external_id'),
        ('Title', 'name'),
        ('QuantityOrdered', 'product_uom_qty'),
    ]

    def _finalize_product_values(self, record, values):
        # This would be a good place to create a vendor or add a route...
        return values

    def _product_sku(self, record):
        # This would be a good place to modify or map the SellerSKU
        return record['SellerSKU']

    def _product_values(self, record):
        sku = self._product_sku(record)
        name = record['Title']
        list_price = float(record.get('ItemPrice', {}).get('Amount', '0.0'))
        values = {
            'default_code': sku,
            'name': name or sku,
            'type': 'product',
            'list_price': list_price,
            'categ_id': self.backend_record.product_categ_id.id,
        }
        return self._finalize_product_values(record, values)

    @mapping
    def product_id(self, record):
        asin = record['ASIN']
        sku = self._product_sku(record)
        binder = self.binder_for('amazon.product.product')
        product = None
        amazon_product = binder.to_internal(sku)
        if amazon_product:
            # keep the asin up to date (or set for the first time!)
            if amazon_product.asin != asin:
                amazon_product.asin = asin
            product = amazon_product.odoo_id  # unwrap
        if not product:
            product = self.env['product.product'].search([
                ('default_code', '=', sku)
            ], limit=1)

        if not product:
            # we could use a record like (0, 0, values)
            product = self.env['product.product'].create(self._product_values(record))
            amazon_product = self.env['amazon.product.product'].create({
                'external_id': sku,
                'odoo_id': product.id,
                'backend_id': self.backend_record.id,
                'asin': asin,
                'state': 'sent',  # Already exists in Amazon
            })

        return {'product_id': product.id}

    @mapping
    def price_unit(self, record):
        # Apparently these are all up, not per-qty
        qty = float(record.get('QuantityOrdered', '1.0')) or 1.0
        price_unit = float(record.get('ItemPrice', {}).get('Amount', '0.0'))
        discount = float(record.get('PromotionDiscount', {}).get('Amount', '0.0'))
        # discount amount needs to be a percent...
        discount = (discount / (price_unit or 1.0)) * 100.0
        return {'price_unit': price_unit / qty, 'discount': discount / qty}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
