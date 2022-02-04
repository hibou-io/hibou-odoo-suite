# © 2021 Hibou Corp.

from io import BytesIO
from base64 import b64encode, b64decode
from json import loads, dumps

from odoo import models, fields, api
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError

FEED_RETRY_PATTERN = {
    1:  1 * 60,
    5:  2 * 60,
    10: 10 * 60,
}


class AmazonFeed(models.Model):
    _name = 'amazon.feed'
    _description = 'Amazon Feed'
    _order = 'id desc'
    _rec_name = 'external_id'

    backend_id = fields.Many2one('amazon.backend', string='Backend')
    external_id = fields.Char(string='Amazon Feed ID')
    type = fields.Selection([
        ('POST_ORDER_FULFILLMENT_DATA', 'Order Fulfillment Data'),
        ('POST_PRODUCT_DATA', 'Product Data'),
        ('POST_INVENTORY_AVAILABILITY_DATA', 'Product Inventory'),
        ('POST_PRODUCT_PRICING_DATA', 'Product Pricing'),
    ], string='Feed Type')
    content_type = fields.Selection([
        ('text/xml', 'XML'),
    ], string='Content Type')
    data = fields.Binary(string='Data', attachment=True)
    response = fields.Binary(string='Response', attachment=True)
    state = fields.Selection([
        ('new', 'New'),
        ('submitted', 'Submitted'),
        ('error_on_submit', 'Submission Error'),
    ], string='State', default='new')
    amazon_state = fields.Selection([
        ('not_sent', ''),
        ('invalid', 'Invalid'),
        ('UNCONFIRMED', 'Request Pending'),
        ('SUBMITTED', 'Submitted'),
        ('IN_SAFETY_NET', 'Safety Net'),
        ('IN_QUEUE', 'Queued'),
        ('IN_PROGRESS', 'Processing'),
        ('DONE', 'Done'),
        ('CANCELLED', 'Cancelled'),
        ('AWAITING_ASYNCHRONOUS_REPLY', 'Awaiting Asynchronous Reply'),
    ], default='not_sent')
    amazon_stock_picking_id = fields.Many2one('amazon.stock.picking',
                                              string='Shipment',
                                              ondelete='set null')
    amazon_product_product_id = fields.Many2one('amazon.product.product',
                                                string='Listing',
                                                ondelete='set null')

    def submit_feed(self):
        for feed in self:
            api_instance = feed.backend_id.get_wrapped_api()
            feeds_api = api_instance.feeds()
            feed_io = BytesIO(b64decode(feed.data))
            res1, res2 = feeds_api.submit_feed(feed.type, feed_io, content_type=feed.content_type)
            feed_id = res2.payload.get('feedId')
            if not feed_id:
                if res2.payload:
                    feed.response = b64encode(dumps(res2.payload))
                feed.state = 'error_on_submit'
            else:
                feed.state = 'submitted'
                feed.external_id = feed_id
                # First attempt will be delayed 1 minute
                # Next 5 retries will be delayed 10 min each
                # The rest will be delayed 30 min each
                feed.with_delay(priority=100).check_feed()

    def check_feed(self):
        for feed in self.filtered('external_id'):
            api_instance = feed.backend_id.get_wrapped_api()
            feeds_api = api_instance.feeds()
            res3 = feeds_api.get_feed(feed.external_id)
            status = res3.payload['processingStatus']
            try:
                feed.amazon_state = status
            except ValueError:
                feed.amazon_state = 'invalid'
            if status in ('IN_QUEUE', 'IN_PROGRESS'):
                raise RetryableJobError('Check back later on: ' + str(status), ignore_retry=True)
            if status in ('DONE', ):
                feed_document_id = res3.payload['resultFeedDocumentId']
                if feed_document_id:
                    response = feeds_api.get_feed_result_document(feed_document_id)
                    try:
                        feed.response = b64encode(response)
                    except TypeError:
                        feed.response = b64encode(response.encode())

                    # queue a job to process the response
                    feed.with_delay(priority=10).process_feed_result()

    def process_feed_result(self):
        for feed in self:
            pass
