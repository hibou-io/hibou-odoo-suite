# © 2021 Hibou Corp.

from base64 import b64decode
from datetime import date, datetime, timedelta
from xml.etree import ElementTree
from .api.feeds import mock_submit_feed_api, mock_check_feed_api
from .common import AmazonTestCase
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields


class TestProductListing(AmazonTestCase):
    def setUp(self):
        super(TestProductListing, self).setUp()
        self.product = self.browse_ref('stock.product_icecream')
        self.amazon_product = self.env['amazon.product.product'].create({
            'external_id': 'Amazon Ice Cream',
            'odoo_id': self.product.id,
            'backend_id': self.backend.id,
            'asin': '',
            'lst_price': 12.99,
        })

    def test_00_create_feed(self):
        self.assertEqual(self.amazon_product.state, 'draft')
        self.amazon_product.button_submit_product()
        self.assertEqual(self.amazon_product.state, 'sent')
        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        merchant_id = root.find('./Header/MerchantIdentifier').text
        self.assertEqual(merchant_id, self.backend.merchant_id)
        product_elem = root.find('./Message/Product')
        self.assertEqual(product_elem.find('SKU').text, self.amazon_product.external_id)

        with mock_submit_feed_api(return_error=True):
            feed.submit_feed()
        self.assertEqual(feed.state, 'error_on_submit')

        with mock_submit_feed_api():
            feed.submit_feed()
        self.assertEqual(feed.state, 'submitted')
        self.assertEqual(feed.external_id, '555555555555')

        with mock_check_feed_api():
            with self.assertRaises(RetryableJobError):
                feed.check_feed()
        self.assertEqual(feed.amazon_state, 'IN_QUEUE')

        with mock_check_feed_api(done=True):
            feed.check_feed()
        self.assertEqual(feed.amazon_state, 'DONE')

    def test_10_update_inventory(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': stock_location.id,
            'quantity': 7.0,
        })

        self.assertFalse(self.amazon_product.date_inventory_sent)
        self.amazon_product.button_update_inventory()
        self.assertEqual(fields.Datetime.from_string(self.amazon_product.date_inventory_sent).date(), date.today())

        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        inventory_elem = root.find('./Message/Inventory')
        self.assertEqual(inventory_elem.find('SKU').text, self.amazon_product.external_id)
        self.assertEqual(float(inventory_elem.find('Quantity').text), 7.0)

    def test_11_update_inventory_global_buffer(self):
        test_qty = 7.0
        global_buffer = 2.0
        self.backend.buffer_qty = global_buffer

        stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': stock_location.id,
            'quantity': test_qty,
        })

        self.assertFalse(self.amazon_product.date_inventory_sent)
        self.amazon_product.button_update_inventory()
        self.assertEqual(fields.Datetime.from_string(self.amazon_product.date_inventory_sent).date(), date.today())

        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        inventory_elem = root.find('./Message/Inventory')
        self.assertEqual(inventory_elem.find('SKU').text, self.amazon_product.external_id)
        self.assertEqual(float(inventory_elem.find('Quantity').text), test_qty - global_buffer)

    def test_12_update_inventory_listing_buffer(self):
        test_qty = 7.0
        global_buffer = 2.0
        product_buffer = 3.0
        self.backend.buffer_qty = global_buffer
        self.amazon_product.buffer_qty = product_buffer

        stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': stock_location.id,
            'quantity': test_qty,
        })

        self.assertFalse(self.amazon_product.date_inventory_sent)
        self.amazon_product.button_update_inventory()
        self.assertEqual(fields.Datetime.from_string(self.amazon_product.date_inventory_sent).date(), date.today())

        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        inventory_elem = root.find('./Message/Inventory')
        self.assertEqual(inventory_elem.find('SKU').text, self.amazon_product.external_id)
        self.assertEqual(float(inventory_elem.find('Quantity').text), test_qty - product_buffer)

    def test_20_update_price_no_pricelist(self):
        self.assertFalse(self.amazon_product.date_price_sent)
        self.amazon_product.button_update_price()
        self.assertEqual(fields.Datetime.from_string(self.amazon_product.date_price_sent).date(), date.today())

        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        price_elem = root.find('./Message/Price')
        self.assertEqual(price_elem.find('SKU').text, self.amazon_product.external_id)
        self.assertEqual(float(price_elem.find('StandardPrice').text), 12.99)
        self.assertIsNone(price_elem.find('SalePrice'))

    def test_30_update_price_with_pricelist(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        self.backend.pricelist_id = self.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'product_tmpl_id': self.product.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': 9.99,
                'date_start': yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_end': tomorrow.strftime(DEFAULT_SERVER_DATE_FORMAT),
            })],
        })

        self.amazon_product.button_update_price()
        feed = self.env['amazon.feed'].search([('amazon_product_product_id', '=', self.amazon_product.id)])
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed.state, 'new')
        self.assertEqual(feed.amazon_state, 'not_sent')
        feed_contents = b64decode(feed.data).decode('iso-8859-1')
        root = ElementTree.fromstring(feed_contents)
        price_elem = root.find('./Message/Price')
        self.assertEqual(price_elem.find('SKU').text, self.amazon_product.external_id)
        self.assertEqual(float(price_elem.find('StandardPrice').text), 12.99)
        sale_elem = price_elem.find('./Sale')
        self.assertEqual(float(sale_elem.find('SalePrice').text), 9.99)
        self.assertEqual(sale_elem.find('StartDate').text, datetime(yesterday.year, yesterday.month, yesterday.day).isoformat())
        self.assertEqual(sale_elem.find('EndDate').text, datetime(tomorrow.year, tomorrow.month, tomorrow.day).isoformat())
