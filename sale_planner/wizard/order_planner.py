from math import sin, cos, sqrt, atan2, radians
from json import dumps, loads
from copy import deepcopy
from datetime import datetime
from logging import getLogger

_logger = getLogger(__name__)

try:
    from uszipcode import ZipcodeSearchEngine
except ImportError:
    _logger.warn('module "uszipcode" cannot be loaded, falling back to Google API')
    ZipcodeSearchEngine = None

from odoo import api, fields, models, tools
from odoo.addons.base_geolocalize.models.res_partner import geo_find, geo_query_address


class FakeCollection():
    def __init__(self, vals):
        self.vals = vals

    def __iter__(self):
        for v in self.vals:
            yield v

    def filtered(self, f):
        return filter(f, self.vals)


class FakePartner():
    def __init__(self, **kwargs):
        """
        'delivery.carrier'.verify_carrier(contact) ->
            country_id,
            state_id,
            zip
            company

        city,

        `distance calculations` ->
            date_localization,
            partner_latitude,
            partner_longitude

            computes them when accessed
        """
        self.partner_latitude = 0.0
        self.partner_longitude = 0.0
        self.is_company = False
        for attr, value in kwargs.items():
            _logger.warn('  ' + str(attr) + ': ' + str(value))
            setattr(self, attr, value)

    @property
    def date_localization(self):
        if not hasattr(self, 'date_localization'):
            self.date_localization = 'TODAY!'
            # The fast way.
            if ZipcodeSearchEngine and self.zip:
                with ZipcodeSearchEngine() as search:
                    zipcode = search.by_zipcode(self.zip)
                    if zipcode:
                        self.partner_latitude = zipcode['Latitude']
                        self.partner_longitude = zipcode['Longitude']
                        return self.date_localization

            # The slow way.
            result = geo_find(geo_query_address(
                city=self.city,
                state=self.state_id.name,
                country=self.country_id.name,
            ))
            if result:
                self.partner_latitude = result[0]
                self.partner_longitude = result[1]

        return self.date_localization


class FakeOrderLine():
    def __init__(self, **kwargs):
        """
        'delivery.carrier'.get_price_available(order) ->
            state,
            is_delivery,
            product_uom._compute_quantity,
            product_uom_qty,
            product_id
            price_total


        """
        self.state = 'draft'
        self.is_delivery = False
        self.product_uom = self

        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def _compute_quantity(self, qty=1, uom=None):
        """
        This is a non-implementation for when someone wants to call product_uom._compute_quantity
        :param qty:
        :param uom:
        :return:
        """
        return qty


class FakeSaleOrder():
    """
    partner_id :: used in shipping
    partner_shipping_id :: is used in several places
    order_line :: can be a FakeCollection of FakeOrderLine's or Odoo 'sale.order.line'
    carrier_id :: can be empty, will be overwritten when walking through carriers

    'delivery.carrier'.get_shipping_price_from_so(orders) ->
        id, (int)
        name, (String)
        currency_id, (Odoo 'res.currency')
        company_id,  (Odoo 'res.company')
        warehouse_id, (Odoo 'stock.warehouse')
        carrier_id, (Odoo 'delivery.carrier')

    SaleOrderMakePlan.generate_shipping_options() ->
        pricelist_id, (Odoo 'product.pricelist')
    """
    def __init__(self, **kwargs):
        self.carrier_id = None
        self.id = 0
        self.name = 'Quote'
        self.team_id = None
        self.project_id = None
        self.amount_total = 0.0
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __iter__(self):
        """
        Emulate a recordset of a single order.
        """
        yield self


def distance(lat_1, lon_1, lat_2, lon_2):
    R = 6373.0

    lat1 = radians(lat_1)
    lon1 = radians(lon_1)
    lat2 = radians(lat_2)
    lon2 = radians(lon_2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


class SaleOrderMakePlan(models.TransientModel):
    _name = 'sale.order.make.plan'
    _description = 'Plan Order'

    order_id = fields.Many2one(
        'sale.order', 'Sale Order',
    )
    planning_option_ids = fields.One2many('sale.order.planning.option', 'plan_id', 'Options')

    @api.model
    def plan_order(self, vals):
        pass

    @api.multi
    def select_option(self, option):
        for plan in self:
            self.plan_order_option(plan.order_id, option)

    def _order_fields_for_option(self, option):
        return {
            'warehouse_id': option.warehouse_id.id,
            'requested_date': option.requested_date,
            'date_planned': option.date_planned,
            'carrier_id': option.carrier_id.id,
        }

    @api.model
    def plan_order_option(self, order, option):
        if option.sub_options:
            sub_options = option.sub_options
            if isinstance(sub_options, str):
                sub_options = loads(sub_options)
            if not isinstance(sub_options, dict):
                _logger.warn('Cannot apply option with corrupt sub_options')
                return False
            order_lines = order.order_line
            for wh_id, wh_vals in sub_options.items():
                wh_id = int(wh_id)
                if wh_id == option.warehouse_id.id:
                    continue
                order_lines.filtered(lambda line: line.product_id.id in wh_vals['product_ids']).write({
                    'warehouse_id': wh_id,
                    'date_planned': wh_vals.get('date_planned'),
                })

        order_fields = self._order_fields_for_option(option)

        order.write(order_fields)

        if option.carrier_id:
            order._create_delivery_line(option.carrier_id, option.shipping_price)


    @api.model
    def create(self, values):
        planner = super(SaleOrderMakePlan, self).create(values)

        for option_vals in self.generate_order_options(planner.order_id):
            option_vals['plan_id'] = planner.id
            planner.planning_option_ids |= self.env['sale.order.planning.option'].create(option_vals)

        return planner

    def _fake_order(self, order):
        return FakeSaleOrder(**{
            'id': order.id,
            'name': order.name,
            'partner_id': order.partner_id,
            'partner_shipping_id': order.partner_shipping_id,
            'order_line': order.order_line,
            'currency_id': order.currency_id,
            'company_id': order.company_id,
            'warehouse_id': order.warehouse_id,
            'amount_total': order.amount_total,
            'pricelist_id': order.pricelist_id,
            'env': self.env,
        })

    @api.model
    def generate_order_options(self, order, plan_shipping=True):
        fake_order = self._fake_order(order)
        base_option = self.generate_base_option(fake_order)
        # do we need shipping?
        # we need to collect it because we want multi-warehouse shipping amounts.
        if order.carrier_id:
            base_option['carrier_id'] = order.carrier_id.id

        if plan_shipping and not self.env.context.get('skip_plan_shipping'):
            options = self.generate_shipping_options(base_option, fake_order)
        else:
            options = [base_option]

        return options

    def get_warehouses(self, warehouse_id=None):
        warehouse = self.env['stock.warehouse'].sudo()
        if warehouse_id:
            return warehouse.search([('id', '=', warehouse_id)])

        if self.env.context.get('warehouse_domain'):
            #potential bug here if this is textual
            return warehouse.search(self.env.context.get('warehouse_domain'))

        irconfig_parameter = self.env['ir.config_parameter'].sudo()
        if irconfig_parameter.get_param('sale.order.planner.warehouse_domain'):
            domain = tools.safe_eval(irconfig_parameter.get_param('sale.order.planner.warehouse_domain'))
            return warehouse.search(domain)

        return warehouse.search([])

    def get_shipping_carriers(self, carrier_id=None):
        Carrier = self.env['delivery.carrier'].sudo()
        if carrier_id:
            return Carrier.search([('id', '=', carrier_id)])

        if self.env.context.get('carrier_domain'):
            # potential bug here if this is textual
            return Carrier.search(self.env.context.get('carrier_domain'))

        irconfig_parameter = self.env['ir.config_parameter'].sudo()
        if irconfig_parameter.get_param('sale.order.planner.carrier_domain'):
            domain = tools.safe_eval(irconfig_parameter.get_param('sale.order.planner.carrier_domain'))
            return Carrier.search(domain)

        return Carrier.search([])

    def generate_base_option(self, order_fake):
        product_lines = list(filter(lambda line: line.product_id.type == 'product', order_fake.order_line))
        if not product_lines:
            return {}

        buy_qty = {line.product_id.id: line.product_uom_qty for line in product_lines}

        products = self.env['product.product']
        for line in product_lines:
            products |= line.product_id

        warehouses = self.get_warehouses()
        product_stock = self._fetch_product_stock(warehouses, products)
        sub_options = {}
        wh_date_planning = {}

        p_len = len(products)
        full_candidates = set()
        partial_candidates = set()
        for wh_id, stock in product_stock.items():
            available = sum(1 for p_id, p_vals in stock.items() if self._is_in_stock(p_vals, buy_qty[p_id]))
            if available == p_len:
                full_candidates.add(wh_id)
            elif available > 0:
                partial_candidates.add(wh_id)

        if full_candidates:
            if len(full_candidates) == 1:
                warehouse = warehouses.filtered(lambda wh: wh.id in full_candidates)
                date_planned = self._next_warehouse_shipping_date(warehouse)
                order_fake.warehouse_id = warehouse
                return {'warehouse_id': warehouse.id, 'date_planned': date_planned}

            warehouse = self._find_closest_warehouse_by_partner(
                warehouses.filtered(lambda wh: wh.id in full_candidates), order_fake.partner_shipping_id)
            date_planned = self._next_warehouse_shipping_date(warehouse)
            order_fake.warehouse_id = warehouse
            return {'warehouse_id': warehouse.id, 'date_planned': date_planned}

        if partial_candidates:
            if len(partial_candidates) == 1:
                warehouse = warehouses.filtered(lambda wh: wh.id in partial_candidates)
                order_fake.warehouse_id = warehouse
                return {'warehouse_id': warehouse.id}

            sorted_warehouses = self._sort_warehouses_by_partner(warehouses.filtered(lambda wh: wh.id in partial_candidates), order_fake.partner_shipping_id)
            primary_wh = sorted_warehouses[0] #partial_candidates means there is at least one warehouse
            primary_wh_date_planned = self._next_warehouse_shipping_date(primary_wh)
            wh_date_planning[primary_wh.id] = primary_wh_date_planned
            for wh in sorted_warehouses:
                if not buy_qty:
                    continue
                stock = product_stock[wh.id]
                for p_id, p_vals in stock.items():
                    if p_id in buy_qty and self._is_in_stock(p_vals, buy_qty[p_id]):
                        if wh.id not in sub_options:
                            sub_options[wh.id] = {
                                'date_planned': self._next_warehouse_shipping_date(wh),
                                'product_ids': [],
                                'product_skus': [],
                            }
                        sub_options[wh.id]['product_ids'].append(p_id)
                        sub_options[wh.id]['product_skus'].append(p_vals['sku'])
                        del buy_qty[p_id]

            if not buy_qty:
                # item_details can fulfil all items.
                # this is good!!
                order_fake.warehouse_id = primary_wh
                return {'warehouse_id': primary_wh.id, 'date_planned': primary_wh_date_planned, 'sub_options': sub_options}

            # warehouses cannot fulfil all requested items!!
            order_fake.warehouse_id = primary_wh
            return {'warehouse_id': primary_wh.id}

        # nobody has stock!
        primary_wh = self._find_closest_warehouse_by_partner(warehouses, order_fake.partner_shipping_id)
        order_fake.warehouse_id = primary_wh
        return {'warehouse_id': primary_wh.id}

    def _is_in_stock(self, p_stock, buy_qty):
        return p_stock['real_qty_available'] >= buy_qty

    def _find_closest_warehouse_by_partner(self, warehouses, partner):
        if not partner.date_localization:
            partner.geo_localize()
        return self._find_closest_warehouse(warehouses, partner.partner_latitude, partner.partner_longitude)

    def _find_closest_warehouse(self, warehouses, latitude, longitude):
        distances = {distance(latitude, longitude, wh.partner_id.partner_latitude, wh.partner_id.partner_longitude): wh.id for wh in warehouses}
        wh_id = distances[min(distances)]
        return warehouses.filtered(lambda wh: wh.id == wh_id)

    def _sort_warehouses_by_partner(self, warehouses, partner):
        if not partner.date_localization:
            partner.geo_localize()
        return self._sort_warehouses(warehouses, partner.partner_latitude, partner.partner_longitude)

    def _sort_warehouses(self, warehouses, latitude, longitude):
        distances = {distance(latitude, longitude, wh.partner_id.partner_latitude, wh.partner_id.partner_longitude): wh.id for wh in warehouses}
        wh_distances = sorted(distances)
        return [warehouses.filtered(lambda wh: wh.id == distances[d]) for d in wh_distances]

    def _next_warehouse_shipping_date(self, warehouse):
        return fields.Datetime.to_string(warehouse.shipping_calendar_id.plan_days(0.01,
                                                                                  fields.Datetime.from_string(fields.Datetime.now()),
                                                                                  compute_leaves=True))

    @api.model
    def _fetch_product_stock(self, warehouses, products):
        output = {}
        for wh in warehouses:
            products = products.with_context({'location': wh.lot_stock_id.id})
            output[wh.id] = {
                p.id: {
                    'qty_available': p.qty_available,
                    'virtual_available': p.virtual_available,
                    'incoming_qty': p.incoming_qty,
                    'outgoing_qty': p.outgoing_qty,
                    'real_qty_available': p.qty_available - p.outgoing_qty,
                    'sku': p.default_code
                } for p in products}
        return output

    def generate_shipping_options(self, base_option, order_fake):
        # generate a carrier_id, amount, requested_date (promise date)
        # if base_option['carrier_id'] then that is the only carrier we want to collect rates for.
        carriers = self.get_shipping_carriers(base_option.get('carrier_id'))

        if not base_option.get('sub_options'):
            options = []
            # this locic comes from "delivery.models.sale_order.SaleOrder"
            for carrier in carriers:
                option = self._generate_shipping_carrier_option(base_option, order_fake, carrier)
                if option:
                    options.append(option)

            return options
        else:
            warehouses = self.get_warehouses()
            original_order_fake_warehouse_id = order_fake.warehouse_id
            original_order_fake_order_line = order_fake.order_line
            options = []
            for carrier in carriers:
                new_base_option = deepcopy(base_option)
                has_error = False
                for wh_id, wh_vals in base_option['sub_options'].items():
                    if has_error:
                        continue
                    order_fake.warehouse_id = warehouses.filtered(lambda wh: wh.id == wh_id)
                    order_fake.order_line = FakeCollection(filter(lambda line: line.product_id.id in wh_vals['product_ids'], original_order_fake_order_line))
                    wh_option = self._generate_shipping_carrier_option(wh_vals, order_fake, carrier)
                    if not wh_option:
                        has_error = True
                    else:
                        new_base_option['sub_options'][wh_id] = wh_option

                if has_error:
                    continue
                # now that we've collected, we can roll up some details.

                new_base_option['carrier_id'] = carrier.id
                new_base_option['shipping_price'] = self._get_shipping_price_for_options(new_base_option['sub_options'])
                new_base_option['requested_date'] = self._get_max_requested_date(new_base_option['sub_options'])
                new_base_option['transit_days'] = self._get_max_transit_days(new_base_option['sub_options'])
                options.append(new_base_option)

            #restore values in case more processing occurs
            order_fake.warehouse_id = original_order_fake_warehouse_id
            order_fake.order_line = original_order_fake_order_line
            if not options:
                options.append(base_option)
            return options

    def _get_shipping_price_for_options(self, sub_options):
        return sum(wh_option.get('shipping_price', 0.0) for wh_option in sub_options.values())

    def _get_max_requested_date(self, sub_options):
        max_requested_date = None
        for option in sub_options.values():
            requested_date = option.get('requested_date')
            if requested_date and isinstance(requested_date, str):
                requested_date = fields.Datetime.from_string(requested_date)
            if requested_date and not max_requested_date:
                max_requested_date = requested_date
            elif requested_date:
                if requested_date > max_requested_date:
                    max_requested_date = requested_date
        if max_requested_date:
            return fields.Datetime.to_string(max_requested_date)
        return max_requested_date

    def _get_max_transit_days(self, sub_options):
        return max(wh_option.get('transit_days', 0) for wh_option in sub_options.values())

    def _generate_shipping_carrier_option(self, base_option, order_fake, carrier):
        # some carriers look at the order carrier_id
        order_fake.carrier_id = carrier

        # this logic comes from "delivery.models.sale_order.SaleOrder"
        try:
            date_delivered = None
            transit_days = 0
            if carrier.delivery_type not in ['fixed', 'base_on_rule']:
                result = carrier.get_shipping_price_for_plan(order_fake, base_option.get('date_planned'))
                if result:
                    price_unit, transit_days, date_delivered = result[0]
                else:
                    price_unit = carrier.get_shipping_price_from_so(order_fake)[0]
            else:
                carrier = carrier.verify_carrier(order_fake.partner_shipping_id)
                if not carrier:
                    return None
                #price_unit = carrier.get_price_available(order)
                # ^^ ends up calling carrier.get_price_from_picking(order_total, weight, volume, quantity)
                order_total = order_fake.amount_total
                weight = sum((line.product_id.weight or 0.0) * line.product_uom_qty for line in order_fake.order_line if line.product_id.type == 'product')
                volume = sum((line.product_id.volume or 0.0) * line.product_uom_qty for line in order_fake.order_line if line.product_id.type == 'product')
                quantity = sum((line.product_uom_qty or 0.0) for line in order_fake.order_line if line.product_id.type == 'product')
                price_unit = carrier.get_price_from_picking(order_total, weight, volume, quantity)
                if order_fake.company_id.currency_id.id != order_fake.pricelist_id.currency_id.id:
                    price_unit = order_fake.company_id.currency_id.with_context(date=order_fake.date_order).compute(price_unit, order_fake.pricelist_id.currency_id)

            final_price = float(price_unit) * (1.0 + (float(carrier.margin) / 100.0))
            option = deepcopy(base_option)
            option['carrier_id'] = carrier.id
            option['shipping_price'] = final_price
            option['requested_date'] = fields.Datetime.to_string(date_delivered) if date_delivered and isinstance(date_delivered, datetime) else date_delivered
            option['transit_days'] = transit_days
            return option
        except Exception as e:
            # _logger.warn("Exception collecting carrier rates: " + str(e))
            # _logger.exception(e)
            pass

        return None



class SaleOrderPlanningOption(models.TransientModel):
    _name = 'sale.order.planning.option'
    _description = 'Order Planning Option'

    def create(self, values):
        if 'sub_options' in values and not isinstance(values['sub_options'], str):
            values['sub_options'] = dumps(values['sub_options'])
        return super(SaleOrderPlanningOption, self).create(values)

    @api.multi
    def _compute_sub_options_text(self):
        for option in self:
            sub_options = option.sub_options
            if sub_options and not isinstance(sub_options, dict):
                sub_options = loads(sub_options)
            if not isinstance(sub_options, dict):
                option.sub_options_text = ''
                continue

            line = ''
            for wh_id, wh_option in sub_options.items():
                product_skus = wh_option.get('product_skus', [])
                product_skus = ', '.join(product_skus)
                requested_date = wh_option.get('requested_date', '')
                if requested_date:
                    requested_date = self._context_datetime(requested_date)
                date_planned = wh_option.get('date_planned', '')
                if date_planned:
                    date_planned = self._context_datetime(date_planned)
                shipping_price = float(wh_option.get('shipping_price', 0.0))
                transit_days = int(wh_option.get('transit_days', 0))

                line += """WH %d :: %s
  Date Planned:   %s
  Requested Date: %s
  Transit Days:   %d
  Shipping Price: %.2f

""" % (int(wh_id), product_skus, date_planned, requested_date, transit_days, shipping_price)

            option.sub_options_text = line

    plan_id = fields.Many2one('sale.order.make.plan', 'Plan', ondelete='cascade')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    date_planned = fields.Datetime('Planned Date')
    requested_date = fields.Datetime('Requested Date')
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier')
    transit_days = fields.Integer('Transit Days')
    shipping_price = fields.Float('Shipping Price')
    sub_options = fields.Text('Sub Options JSON')
    sub_options_text = fields.Text('Sub Options', compute=_compute_sub_options_text)

    @api.multi
    def select_plan(self):
        for option in self:
            option.plan_id.select_option(option)
            return

    def _context_datetime(self, date):
        date = fields.Datetime.from_string(date)
        date = fields.Datetime.context_timestamp(self, date)
        return fields.Datetime.to_string(date)
