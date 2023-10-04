# © 2019-2022 Hibou Corp.

from copy import copy
from html import unescape
from datetime import datetime, timedelta
import logging

from odoo import fields, _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.exception import RetryableJobError, NothingToDoJob, FailedJobError


_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    _name = 'opencart.sale.order.batch.importer'
    _inherit = 'opencart.delayed.batch.importer'
    _apply_on = 'opencart.sale.order'

    def _import_record(self, external_id, store_id, job_options=None, **kwargs):
        if not job_options:
            job_options = {
                'max_retries': 0,
                'priority': 5,
            }
        # It is very likely that we already have this order because we may have just uploaded a tracking number
        # We want to avoid creating queue jobs for orders already imported.
        order_binder = self.binder_for('opencart.sale.order')
        order = order_binder.to_internal(external_id)
        if order:
            _logger.warning('Order (%s) already imported.' % (order.name, ))
            return
        if store_id is not None:
            store_binder = self.binder_for('opencart.store')
            store = store_binder.to_internal(store_id).sudo()
            if not store.enable_order_import:
                _logger.warning('Store (%s) is not enabled for Sale Order import (%s).' % (store.name, external_id))
                return
            user = store.warehouse_id.company_id.user_tech_id
            if user and user != self.env.user:
                # Note that this is a component, which has an env through it's 'collection'
                # however, when importing the 'model' is actually what runs the delayed job
                env = self.env(user=user)
                self.collection.env = env
                self.model.env = env
        return super(SaleOrderBatchImporter, self)._import_record(
            external_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = {}
        external_ids = list(self.backend_adapter.search(filters))
        for ids in external_ids:
            _logger.debug('run._import_record for %s' % (ids, ))
            self._import_record(ids[0], ids[1])
        if external_ids:
            last_id = list(sorted(external_ids, key=lambda i: i[0]))[-1][0]
            last_date = list(sorted(external_ids, key=lambda i: i[2]))[-1][2]
            self.backend_record.write({
                'import_orders_after_id': last_id,
                'import_orders_after_date': self.backend_record.date_to_odoo(last_date),
            })


class SaleOrderImportMapper(Component):
    _name = 'opencart.sale.order.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = 'opencart.sale.order'

    direct = [('order_id', 'external_id'),
              ('store_id', 'store_id'),
              ('comment', 'note'),
              ]

    children = [('products', 'opencart_order_line_ids', 'opencart.sale.order.line'),
                ]

    def _add_coupon_lines(self, map_record, values):
        # Data from API
        # 'coupons': [{'amount': '7.68', 'code': '1111'}],
        record = map_record.source

        coupons = record.get('coupons')
        if not coupons:
            return values

        coupon_product = self.options.store.coupon_product_id or self.backend_record.coupon_product_id
        if not coupon_product:
            coupon_product = self.env.ref('connector_ecommerce.product_product_discount', raise_if_not_found=False)

        if not coupon_product:
            raise ValueError('Coupon %s on order requires coupon product in configuration.' % (coupons, ))
        for coupon in coupons:
            line_builder = self.component(usage='order.line.builder')
            line_builder.price_unit = -float(coupon.get('amount', 0.0))
            line_builder.product = coupon_product
            # `order.line.builder` does not allow naming.
            line_values = line_builder.get_line()
            code = coupon.get('code')
            if code:
                line_values['name'] = '%s Code: %s' % (coupon_product.name, code)
            values['order_line'].append((0, 0, line_values))
        return values

    def _add_shipping_line(self, map_record, values):
        record = map_record.source

        line_builder = self.component(usage='order.line.builder.shipping')
        line_builder.price_unit = record.get('shipping_exclude_tax', 0.0)

        if values.get('carrier_id'):
            carrier = self.env['delivery.carrier'].browse(values['carrier_id'])
            line_builder.product = carrier.product_id
            line = (0, 0, line_builder.get_line())
            values['order_line'].append(line)

        return values

    def finalize(self, map_record, values):
        values.setdefault('order_line', [])
        self._add_coupon_lines(map_record, values)
        self._add_shipping_line(map_record, values)
        values.update({
            'partner_id': self.options.partner_id,
            'partner_invoice_id': self.options.partner_invoice_id,
            'partner_shipping_id': self.options.partner_shipping_id,
        })
        onchange = self.component(
            usage='ecommerce.onchange.manager.sale.order'
        )
        return onchange.play(values, values['opencart_order_line_ids'])

    @mapping
    def name(self, record):
        name = str(record['order_id'])
        prefix = self.options.store.sale_prefix or self.backend_record.sale_prefix
        if prefix:
            name = prefix + name
        return {'name': name}

    @mapping
    def date_order(self, record):
        date_added = record.get('date_added')
        if date_added:
            date_added = self.backend_record.date_to_odoo(date_added)
        return {'date_order': date_added or fields.Datetime.now()}

    @mapping
    def fiscal_position_id(self, record):
        fiscal_position = self.options.store.fiscal_position_id or self.backend_record.fiscal_position_id
        if fiscal_position:
            return {'fiscal_position_id': fiscal_position.id}

    @mapping
    def team_id(self, record):
        team = self.options.store.team_id or self.backend_record.team_id
        if team:
            return {'team_id': team.id}

    @mapping
    def payment_mode_id(self, record):
        record_method = record['payment_method']
        method = self.env['account.payment.mode'].search(
            [('name', '=', record_method)],
            limit=1,
        )
        if not method:
            raise ValueError('Payment Mode named "%s", cannot be found.' % (record_method, ))
        return {'payment_mode_id': method.id}

    @mapping
    def project_id(self, record):
        analytic_account = self.options.store.analytic_account_id or self.backend_record.analytic_account_id
        if analytic_account:
            return {'project_id': analytic_account.id}

    @mapping
    def warehouse_id(self, record):
        warehouse = self.options.store.warehouse_id or self.backend_record.warehouse_id
        if warehouse:
            return {'warehouse_id': warehouse.id}

    @mapping
    def shipping_code(self, record):
        method = record.get('shipping_code') or record.get('shipping_method')
        if not method:
            return {'carrier_id': False}

        carrier_domain = [('opencart_code', '=', method.strip())]
        company = self.options.store.company_id or self.backend_record.company_id
        if company:
            carrier_domain += [
                '|', ('company_id', '=', company.id), ('company_id', '=', False)
            ]
        carrier = self.env['delivery.carrier'].search(carrier_domain, limit=1)
        if not carrier:
            raise ValueError('Delivery Carrier for method Code "%s", cannot be found.' % (method, ))
        return {'carrier_id': carrier.id}

    @mapping
    def company_id(self, record):
        company = self.options.store.company_id or self.backend_record.company_id
        if not company:
            raise ValidationError('Company not found in Opencart Backend or Store')
        return {'company_id': company.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def total_amount(self, record):
        total_amount = record['total']
        return {'total_amount': total_amount}


class SaleOrderImporter(Component):
    _name = 'opencart.sale.order.importer'
    _inherit = 'opencart.importer'
    _apply_on = 'opencart.sale.order'

    def _must_skip(self):
        if self.binder.to_internal(self.external_id):
            return _('Already imported')

    def _before_import(self):
        rules = self.component(usage='sale.import.rule')
        rules.check(self.opencart_record)

    def _create_partner(self, values):
        return self.env['res.partner'].create(values)

    def _partner_matches(self, partner, values):
        for key, value in values.items():
            if key in ('active', 'parent_id', 'type'):
                continue

            if key == 'state_id':
                if value != partner.state_id.id:
                    return False
            elif key == 'country_id':
                if value != partner.country_id.id:
                    return False
            elif bool(value) and isinstance(value, str):
                if value.lower() != str(getattr(partner, key)).lower():
                    return False
            elif bool(value) and value != getattr(partner, key):
                return False
        return True

    def _make_partner_name(self, firstname, lastname, other_values=None):
        name = (str(firstname or '').strip() + ' ' + str(lastname or '').strip()).strip()
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


        name = self._make_partner_name(info.get('firstname', ''), info.get('lastname', ''), other_values=info)
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
            'email': email.strip(),
            'name': name.strip(),
            'phone': phone.strip(),
            'street': street.strip(),
            'street2': street2.strip(),
            'zip': zip_.strip(),
            'city': city.strip(),
            'state_id': state.id,
            'country_id': country.id,
        }

    def _import_addresses(self):
        partner_values = self._get_partner_values()
        # If they only buy services, then the shipping details will be empty
        if partner_values.get('name', 'Undefined') == 'Undefined':
            partner_values = self._get_partner_values(info_string='payment_')

        partners = self.env['res.partner'].search([
            ('email', '=ilike', partner_values['email']),
            '|', ('active', '=', False), ('active', '=', True),
        ], order='active DESC, id ASC')

        partner = None
        for possible in partners:
            if self._partner_matches(possible, partner_values):
                partner = possible
                break
        if not partner and partners:
            partner = partners[0]

        if not partner:
            # create partner.
            partner = self._create_partner(copy(partner_values))

        if not self._partner_matches(partner, partner_values):
            partner_values['parent_id'] = partner.id
            shipping_values = copy(partner_values)
            shipping_values['type'] = 'delivery'
            shipping_partner = self._create_partner(shipping_values)
        else:
            shipping_partner = partner

        invoice_values = self._get_partner_values(info_string='payment_')
        invoice_values['type'] = 'invoice'

        if (not self._partner_matches(partner, invoice_values)
                and not self._partner_matches(shipping_partner, invoice_values)):
            # Try to find existing invoice address....
            for possible in partners:
                if self._partner_matches(possible, invoice_values):
                    invoice_partner = possible
                    break
            else:
                invoice_values['parent_id'] = partner.id
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

    def _get_store(self, record):
        store_binder = self.binder_for('opencart.store')
        return store_binder.to_internal(record['store_id'])

    def _create_data(self, map_record, **kwargs):
        # non dependencies
        # our current handling of partners doesn't require anything special for the store
        self._check_special_fields()
        store = self._get_store(map_record.source)
        return super(SaleOrderImporter, self)._create_data(
            map_record,
            partner_id=self.partner.id,
            partner_invoice_id=self.invoice_partner.id,
            partner_shipping_id=self.shipping_partner.id,
            store=store,
            **kwargs
        )

    def _order_comment_review(self, binding):
        review_group = self.env.ref('connector_opencart.group_order_comment_review', raise_if_not_found=False)
        if review_group and binding.note:
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            activity_type_id = activity_type.id if activity_type else False
            for user in review_group.users:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type_id,
                    'summary': 'Order Comment Review',
                    'note': '<p>' + binding.note + '</p>',  # field is HTML, note is expected to be escaped
                    'user_id': user.id,
                    'res_id': binding.odoo_id.id,
                    'res_model_id': self.env.ref('sale.model_sale_order').id,
                })

    def _create(self, data):
        binding = super(SaleOrderImporter, self)._create(data)
        self._order_comment_review(binding)

        return binding

    def _import_dependencies(self):
        record = self.opencart_record
        self._import_addresses()
        products_need_setup = []
        for product in record.get('products', []):
            if 'product_id' in product and product['product_id']:
                needs_product_setup = self._import_dependency(product['product_id'], 'opencart.product.template')
                if needs_product_setup:
                    products_need_setup.append(product['product_id'])

        if products_need_setup and self.backend_record.so_require_product_setup:
            # There are products that were either just imported, or
            raise RetryableJobError('Products need setup. OpenCart Product IDs:' + str(products_need_setup), seconds=3600)

    def _after_import(self, binding):
        super(SaleOrderImporter, self)._after_import(binding)
        # Recompute taxes
        binding.odoo_id._recompute_taxes()
        # Recompute prices? not for now, use the prices from the original order
        # binding.odoo_id._recompute_prices()

class SaleImportRule(Component):
    _name = 'opencart.sale.import.rule'
    _inherit = 'base.opencart.connector'
    _apply_on = 'opencart.sale.order'
    _usage = 'sale.import.rule'
    
    _status_no_import = [
        'Canceled',
        'Canceled Reversal',
        'Chargeback',
        'Denied',
        'Expired',
        'Failed',
        'Refunded',
        'Reversed',
        'Voided',
    ]
    
    _status_import_later = [
        'Pending',
        'Processing',
    ]

    def _rule_always(self, record, method):
        """ Always import the order """
        return True
    
    def _rule_check_status(self, record, method):
        order_status = record['order_status']
        if order_status in self._status_import_later:
            order_id = record['order_id']
            raise RetryableJobError('Order %s is in %s and will be re-tried later.' % (order_id, order_status))
        return True

    def _rule_never(self, record, method):
        """ Never import the order """
        raise NothingToDoJob('Orders with payment method %s are never imported.' % method.name)

    # currently, no good way of knowing if an order is paid or authorized
    # we use these both to indicate you only want to import it if it makes it 
    # past a pending/processing state (the order itself)
    _rules = {'always': _rule_always,
              'paid': _rule_check_status,
              'authorized': _rule_check_status,
              'never': _rule_never,
              }
    
    def _rule_global(self, record, method):
        """ Rule always executed, whichever is the selected rule.
        Discards orders based on it being in a canceled state or status.
        Discards orders based on order date being outside of import window."""
        order_id = record['order_id']
        order_status = record['order_status']
        if order_status in self._status_no_import:
            raise NothingToDoJob('Order %s not imported for status %s' % (order_id, order_status))
        max_days = method.days_before_cancel
        if max_days:
            order_date = self.backend_record.date_to_odoo(record['date_added'])
            if order_date + timedelta(days=max_days) < datetime.now():
                raise NothingToDoJob('Import of the order %s canceled '
                                     'because it has not been paid since %d '
                                     'days' % (order_id, max_days))

    def check(self, record):
        """ Check whether the current sale order should be imported
        or not. It will actually use the payment method configuration
        and see if the choosed rule is fullfilled.
        :returns: True if the sale order should be imported
        :rtype: boolean
        """
        record_method = record['payment_method']
        method = self.env['account.payment.mode'].search(
            [('name', '=', record_method)],
            limit=1,
        )
        if not method:
            raise FailedJobError('Payment Mode named "%s", cannot be found.' % (record_method, ))
        self._rule_global(record, method)
        self._rules[method.import_rule](self, record, method)


class SaleOrderLineImportMapper(Component):

    _name = 'opencart.sale.order.line.mapper'
    _inherit = 'opencart.import.mapper'
    _apply_on = 'opencart.sale.order.line'

    direct = [('quantity', 'product_uom_qty'),
              ('price', 'price_unit'),
              ('order_product_id', 'external_id'),
              ]

    # Note mapping for name is removed due to desire to get 
    # custom attr values to display via computed sol description
    @mapping
    def product_id(self, record):
        product_id = record['product_id']
        binder = self.binder_for('opencart.product.template')
        # do not unwrap, because it would be a product.template, but I need a specific variant
        # connector bindings are found with `active_test=False` but that also means computed fields
        # like `product.template.product_variant_id` could find different products because of archived variants
        opencart_product_template = binder.to_internal(product_id, unwrap=False).with_context(active_test=True)
        line_options = record.get('option') or []
        options_for_product = list(filter(lambda o: o.get('product_option_value_id'), line_options))
        options_for_line = list(filter(lambda o: not o.get('product_option_value_id'), line_options))
        product = opencart_product_template.opencart_sale_get_combination(options_for_product)

        custom_option_commands = opencart_product_template.opencart_sale_line_custom_value_commands(options_for_line)
        return {
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_custom_attribute_value_ids': custom_option_commands,
        }
