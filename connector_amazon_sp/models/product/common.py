# © 2021 Hibou Corp.

from base64 import b64encode
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.component.core import Component

PRODUCT_SKU_WITH_WAREHOUSE = '%s-%s'


class AmazonProductProduct(models.Model):
    _name = 'amazon.product.product'
    _inherit = 'amazon.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'Amazon Product Listing'
    _rec_name = 'external_id'

    odoo_id = fields.Many2one('product.product',
                              string='Product',
                              required=True,
                              ondelete='cascade')
    asin = fields.Char(string='ASIN')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Submitted'),
    ], default='draft')
    warehouse_id = fields.Many2one('stock.warehouse',
                                   string='Warehouse',
                                   ondelete='set null')
    backend_warehouse_ids = fields.Many2many(related='backend_id.warehouse_ids')
    backend_fba_warehouse_ids = fields.Many2many(related='backend_id.fba_warehouse_ids')
    date_product_sent = fields.Datetime(string='Last Product Update')
    date_price_sent = fields.Datetime(string='Last Price Update')
    date_inventory_sent = fields.Datetime(string='Last Inventory Update')
    buffer_qty = fields.Integer(string='Buffer Quantity',
                                help='Stock to hold back from Amazon for listings. (-1 means use the backend default)',
                                default=-1)

    @api.onchange('odoo_id', 'warehouse_id', 'default_code')
    def _onchange_suggest_external_id(self):
        with_code_and_warehouse = self.filtered(lambda p: p.default_code and p.warehouse_id)
        with_code = (self - with_code_and_warehouse).filtered('default_code')
        other = (self - with_code_and_warehouse - with_code)
        for product in with_code_and_warehouse:
            product.external_id = PRODUCT_SKU_WITH_WAREHOUSE % (product.default_code, product.warehouse_id.code)
        for product in with_code:
            product.external_id = product.default_code
        for product in other:
            product.external_id = product.external_id

    def button_submit_product(self):
        backends = self.mapped('backend_id')
        for backend in backends:
            products = self.filtered(lambda p: p.backend_id == backend)
            products._submit_product()
        return 1

    def button_update_inventory(self):
        backends = self.mapped('backend_id')
        for backend in backends:
            products = self.filtered(lambda p: p.backend_id == backend)
            products._update_inventory()
        return 1

    def button_update_price(self):
        backends = self.mapped('backend_id')
        for backend in backends:
            products = self.filtered(lambda p: p.backend_id == backend)
            products._update_price()
        return 1

    def _submit_product(self):
        # this should be called on a product set that has the same backend
        backend = self[0].backend_id
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='amazon.product.product.exporter')
            exporter.run(self)
            self.write({'date_product_sent': fields.Datetime.now(), 'state': 'sent'})

    def _update_inventory(self):
        # this should be called on a product set that has the same backend
        backend = self[0].backend_id
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='amazon.product.product.exporter')
            exporter.run_inventory(self)
            self.write({'date_inventory_sent': fields.Datetime.now()})

    def _update_price(self):
        # this should be called on a product set that has the same backend
        backend = self[0].backend_id
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='amazon.product.product.exporter')
            exporter.run_price(self)
            self.write({'date_price_sent': fields.Datetime.now()})

    def _update_for_backend_products(self, backend):
        return self.search([
            ('backend_id', '=', backend.id),
            ('state', '=', 'sent'),
        ])

    def update_inventory(self, backend):
        products = self._update_for_backend_products(backend)
        if products:
            products._update_inventory()

    def update_price(self, backend):
        products = self._update_for_backend_products(backend)
        if products:
            products._update_price()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    amazon_bind_ids = fields.One2many('amazon.product.product', 'odoo_id', string='Amazon Listings')


class ProductAdapter(Component):
    _name = 'amazon.product.product.adapter'
    _inherit = 'amazon.adapter'
    _apply_on = 'amazon.product.product'

    def _api(self):
        return self.api_instance.feeds()

    def _submit_feed(self, bindings, type, content_type, data):
        feed_values = {
            'backend_id': bindings[0].backend_id.id,
            'type': type,
            'content_type': content_type,
            'data': b64encode(data),
        }
        if len(bindings) == 1:
            feed_values['amazon_product_product_id'] = bindings.id
        feed = self.env['amazon.feed'].create(feed_values)
        feed.with_delay(priority=19).submit_feed()  # slightly higher than regular submit_feed calls
        return feed

    def create(self, bindings):
        feed_root, _message = self._product_data_feed(bindings)
        feed_data = self._feed_string(feed_root)
        self._submit_feed(bindings, 'POST_PRODUCT_DATA', 'text/xml', feed_data)

    def create_inventory(self, bindings):
        feed_root, _message = self._product_inventory_feed(bindings)
        feed_data = self._feed_string(feed_root)
        self._submit_feed(bindings, 'POST_INVENTORY_AVAILABILITY_DATA', 'text/xml', feed_data)

    def create_price(self, bindings):
        feed_root, _message = self._product_price_feed(bindings)
        feed_data = self._feed_string(feed_root)
        self._submit_feed(bindings, 'POST_PRODUCT_PRICING_DATA', 'text/xml', feed_data)

    def _process_product_data(self, bindings):
        res = []
        for amazon_product in bindings:
            # why iterate? because we probably need more data eventually...
            if not amazon_product.external_id:
                raise UserError('Amazon Product Listing (%s) must have an Amazon SKU filled.' % (amazon_product.id, ))
            res.append({
                'SKU': amazon_product.external_id,
            })
        return res

    def _product_data_feed(self, bindings):
        product_datas = self._process_product_data(bindings)
        root, message = self._feed('Product', bindings[0].backend_id)
        root.remove(message)
        self.ElementTree.SubElement(root, 'PurgeAndReplace').text = 'false'
        for i, product_data in enumerate(product_datas, 1):
            message = self.ElementTree.SubElement(root, 'Message')
            self.ElementTree.SubElement(message, 'MessageID').text = str(i)
            # ElementTree.SubElement(message, 'OperationType').text = 'Update'
            self.ElementTree.SubElement(message, 'OperationType').text = 'PartialUpdate'
            product = self.ElementTree.SubElement(message, 'Product')
            self.ElementTree.SubElement(product, 'SKU').text = product_data['SKU']
            # standard_product_id = ElementTree.SubElement(product, 'StandardProductID')
            # ElementTree.SubElement(standard_product_id, 'Type').text = product_data['StandardProductID.Type']
            # ElementTree.SubElement(standard_product_id, 'Value').text = product_data['StandardProductID.Value']
            # description_data = ElementTree.SubElement(product, 'DescriptionData')
            # ElementTree.SubElement(description_data, 'Title').text = product_data['Title']
            # ElementTree.SubElement(description_data, 'Brand').text = product_data['Brand']
            # ElementTree.SubElement(description_data, 'Description').text = product_data['Description']
            # for bullet in product_data['BulletPoints']:
            #     ElementTree.SubElement(description_data, 'BulletPoint').text = bullet
            # ElementTree.SubElement(description_data, 'Manufacturer').text = product_data['Manufacturer']
            # ElementTree.SubElement(description_data, 'ItemType').text = product_data['ItemType']
        return root, message

    def _process_product_inventory(self, bindings):
        def _qty(binding, buffer_qty):
            # qty available is all up inventory, less outgoing inventory gives qty to send
            qty = binding.qty_available - binding.outgoing_qty
            if binding.buffer_qty >= 0.0:
                return max((0.0, qty - binding.buffer_qty))
            return max((0.0, qty - buffer_qty))

        res = []
        backend = bindings[0].backend_id
        backend_warehouses = backend.warehouse_ids
        backend_fba_warehouses = backend.fba_warehouse_ids
        warehouses = bindings.mapped('warehouse_id')
        for warehouse in warehouses:
            wh_bindings = bindings.filtered(lambda p: p.warehouse_id == warehouse).with_context(warehouse=warehouse.id)
            buffer_qty = backend.fba_buffer_qty if warehouse in backend_fba_warehouses else backend.buffer_qty
            for binding in wh_bindings:
                res.append((binding.external_id, _qty(binding, buffer_qty)))

        buffer_qty = backend.buffer_qty
        for binding in bindings.filtered(lambda p: not p.warehouse_id).with_context(warehouse=backend_warehouses.ids):
            res.append((binding.external_id, _qty(binding, buffer_qty)))
        return res

    def _product_inventory_feed(self, bindings):
        product_datas = self._process_product_inventory(bindings)
        root, message = self._feed('Inventory', bindings[0].backend_id)
        root.remove(message)
        for i, product_data in enumerate(product_datas, 1):
            sku, qty = product_data
            message = self.ElementTree.SubElement(root, 'Message')
            self.ElementTree.SubElement(message, 'MessageID').text = str(i)
            # ElementTree.SubElement(message, 'OperationType').text = 'Update'
            self.ElementTree.SubElement(message, 'OperationType').text = 'Update'
            inventory = self.ElementTree.SubElement(message, 'Inventory')
            self.ElementTree.SubElement(inventory, 'SKU').text = sku
            self.ElementTree.SubElement(inventory, 'Quantity').text = str(int(qty))
        return root, message

    def _process_product_price(self, bindings):
        def _process_product_price_internal(env, binding, pricelist, res):
            price = binding.lst_price
            sale_price = None
            date_start = None
            date_end = None
            if pricelist:
                rule = None
                sale_price, rule_id = pricelist.get_product_price_rule(binding.odoo_id, 1.0, None)
                if rule_id:
                    rule = env['product.pricelist.item'].browse(rule_id).exists()
                if rule and (rule.date_start or rule.date_end):
                    date_start = rule.date_start
                    date_end = rule.date_end
            res.append((binding.external_id, price, sale_price, date_start, date_end))

        res = []
        backend = bindings[0].backend_id
        pricelist = backend.pricelist_id
        fba_pricelist = backend.fba_pricelist_id
        backend_fba_warehouses = backend.fba_warehouse_ids
        fba_bindings = bindings.filtered(lambda b: b.warehouse_id and b.warehouse_id in backend_fba_warehouses)
        for binding in fba_bindings:
            _process_product_price_internal(self.env, binding, fba_pricelist, res)
        for binding in (bindings - fba_bindings):
            _process_product_price_internal(self.env, binding, pricelist, res)
        return res

    def _product_price_feed(self, bindings):
        backend = bindings[0].backend_id
        product_datas = self._process_product_price(bindings)
        root, message = self._feed('Price', backend)
        root.remove(message)
        now = fields.Datetime.now()
        tomorrow = str(fields.Datetime.from_string(now) + timedelta(days=1))

        for i, product_data in enumerate(product_datas, 1):
            sku, _price, _sale_price, date_start, date_end = product_data
            message = self.ElementTree.SubElement(root, 'Message')
            self.ElementTree.SubElement(message, 'MessageID').text = str(i)
            # ElementTree.SubElement(message, 'OperationType').text = 'Update'
            # self.ElementTree.SubElement(message, 'OperationType').text = 'Update'
            price = self.ElementTree.SubElement(message, 'Price')
            self.ElementTree.SubElement(price, 'SKU').text = sku
            standard_price = self.ElementTree.SubElement(price, 'StandardPrice')
            standard_price.text = '%0.2f' % (_price, )
            standard_price.attrib['currency'] = 'USD'  # TODO gather currency
            if _sale_price and abs(_price - _sale_price) > 0.01:
                sale = self.ElementTree.SubElement(price, 'Sale')
                if not date_start:
                    date_start = now
                self.ElementTree.SubElement(sale, 'StartDate').text = fields.Datetime.from_string(date_start).isoformat()
                if not date_end:
                    date_end = tomorrow
                self.ElementTree.SubElement(sale, 'EndDate').text = fields.Datetime.from_string(date_end).isoformat()
                sale_price = self.ElementTree.SubElement(sale, 'SalePrice')
                sale_price.text = '%0.2f' % (_sale_price, )
                sale_price.attrib['currency'] = 'USD'  # TODO gather currency
        return root, message
