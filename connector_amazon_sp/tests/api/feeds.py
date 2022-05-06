from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from sp_api.base.ApiResponse import ApiResponse
from unittest.mock import patch


@contextmanager
def mock_submit_feed_api(return_error=False):

    submit_feed_res1 = {'errors': None,
                        'headers': {'Content-Length': '665',
                                    'Content-Type': 'application/json',
                                    'Date': datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:00 %Z'),
                                    },
                        'kwargs': {},
                        'next_token': None,
                        'pagination': None,
                        'payload': {'encryptionDetails': {'initializationVector': '',
                                                          'key': '',
                                                          'standard': 'AES'},
                                    'feedDocumentId': '',
                                    'url': ''}}

    submit_feed_res2 = {'errors': None,
                        'headers': {'Content-Length': '37',
                                    'Content-Type': 'application/json',
                                    'Date': datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:00 %Z'),
                                    },
                        'kwargs': {},
                        'next_token': None,
                        'pagination': None,
                        'payload': {'feedId': '555555555555'}}
    if return_error:
        submit_feed_res2['payload'] = {}

    with patch('odoo.addons.connector_amazon_sp.components.api.amazon.Feeds') as mock_feeds:
        mock_feeds.return_value.submit_feed.return_value = ApiResponse(**submit_feed_res1), ApiResponse(**submit_feed_res2)
        yield

@contextmanager
def mock_check_feed_api(done=False):
    check_feed_res3 = {'errors': None,
                       'headers': {'Content-Length': '175', 'Content-Type': 'application/json',
                                   'Date': datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:00 %Z')},
                       'kwargs': {},
                       'next_token': None,
                       'pagination': None,
                       'payload': {'createdTime': datetime.now(tz=timezone.utc).isoformat(timespec='seconds'),
                                   'feedId': '555555555555',
                                   'feedType': 'POST_PRODUCT_DATA',
                                   'marketplaceIds': ['555555555555'],
                                   'processingStatus': 'IN_QUEUE'}}
    if done:
        check_feed_res3['payload']['processingStatus'] = 'DONE'
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=2)
        check_feed_res3['payload']['processingStartTime'] = start_time.isoformat(timespec='seconds')
        check_feed_res3['payload']['processingEndTime'] = end_time.isoformat(timespec='seconds')
        check_feed_res3['payload']['resultFeedDocumentId'] = 'xxxxxxxx'

    feed_result_document = """
<?xml version="1.0" encoding="UTF-8"?>
<AmazonEnvelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="amzn-envelope.xsd">
    <Header>
        <DocumentVersion>1.02</DocumentVersion>
        <MerchantIdentifier>555555555555</MerchantIdentifier>
    </Header>
    <MessageType>ProcessingReport</MessageType>
    <Message>
    <MessageID>1</MessageID>
        <ProcessingReport>
            <DocumentTransactionID>555555555555</DocumentTransactionID>
            <StatusCode>Complete</StatusCode>
            <ProcessingSummary>
                <MessagesProcessed>1</MessagesProcessed>
                <MessagesSuccessful>1</MessagesSuccessful>
                <MessagesWithError>0</MessagesWithError>
                <MessagesWithWarning>0</MessagesWithWarning>
            </ProcessingSummary>
        </ProcessingReport>
    </Message>
</AmazonEnvelope>
    """

    with patch('odoo.addons.connector_amazon_sp.components.api.amazon.Feeds') as mock_feeds:
        mock_feeds.return_value.get_feed.return_value = ApiResponse(**check_feed_res3)
        mock_feeds.return_value.get_feed_result_document.return_value = feed_result_document
        yield
