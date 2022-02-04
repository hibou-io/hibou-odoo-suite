from contextlib import contextmanager
from sp_api.base.ApiResponse import ApiResponse
from unittest.mock import patch

get_order_response = {'payload': {'AmazonOrderId': '111-1111111-1111111',
                                  'PurchaseDate': '2021-04-24T20:22:03Z',
                                  'LastUpdateDate': '2021-04-26T17:25:41Z',
                                  'OrderStatus': 'Shipped',
                                  'FulfillmentChannel': 'MFN',
                                  'SalesChannel': 'Amazon.com',
                                  'ShipServiceLevel': 'Std US D2D Dom',
                                  'OrderTotal': {'CurrencyCode': 'USD',
                                                 'Amount': '159.96'},
                                  'NumberOfItemsShipped': 1,
                                  'NumberOfItemsUnshipped': 0,
                                  'PaymentMethod': 'Other',
                                  'PaymentMethodDetails': ['Standard'],
                                  'IsReplacementOrder': False,
                                  'MarketplaceId': 'ATVPDKIKX0DER',
                                  'ShipmentServiceLevelCategory': 'Standard',
                                  'OrderType': 'StandardOrder',
                                  'EarliestShipDate': '2021-04-26T07:00:00Z',
                                  'LatestShipDate': '2021-04-27T06:59:59Z',
                                  'EarliestDeliveryDate': '2021-04-30T07:00:00Z',
                                  'LatestDeliveryDate': '2021-05-01T06:59:59Z',
                                  'IsBusinessOrder': False,
                                  'IsPrime': True,
                                  'IsGlobalExpressEnabled': False,
                                  'IsPremiumOrder': False,
                                  'IsSoldByAB': False,
                                  'DefaultShipFromLocationAddress': {'Name': 'null',
                                                                     'AddressLine1': 'null',
                                                                     'AddressLine2': 'null',
                                                                     'City': 'SELLERSBURG',
                                                                     'StateOrRegion': 'IN',
                                                                     'PostalCode': '47172',
                                                                     'CountryCode': 'US'},
                                  'IsISPU': False}}

get_order_items_response = {'payload': {'AmazonOrderId': '111-1111111-1111111',
                                        'OrderItems': [
                                            {'ASIN': 'A1B1C1D1E1',
                                             'OrderItemId': '12345678901234',
                                             'SellerSKU': 'TEST_PRODUCT',
                                             'Title': 'Test Product Purchased From Amazon',
                                             'QuantityOrdered': 1, 'QuantityShipped': 1,
                                             'ProductInfo': {'NumberOfItems': '1'},
                                             'ItemPrice': {'CurrencyCode': 'USD', 'Amount': '199.95'},
                                             'ItemTax': {'CurrencyCode': 'USD', 'Amount': '0.00'},
                                             'PromotionDiscount': {'CurrencyCode': 'USD', 'Amount': '39.99'},
                                             'PromotionDiscountTax': {'CurrencyCode': 'USD', 'Amount': '0.00'},
                                             'PromotionIds': ['Coupon'],
                                             'IsGift': 'false',
                                             'ConditionId': 'New',
                                             'ConditionSubtypeId': 'New',
                                             'IsTransparency': False}]}}

get_order_address_response = {'payload': {'AmazonOrderId': '111-1111111-1111111',
                                          'ShippingAddress': {'StateOrRegion': 'FL', 'PostalCode': '34655-5649',
                                                              'City': 'NEW PORT RICHEY', 'CountryCode': 'US',
                                                              'Name': ''}}}

get_order_buyer_info_response = {'payload': {'AmazonOrderId': '111-1111111-1111111',
                                             'BuyerEmail': 'obfuscated@marketplace.amazon.com'}}


@contextmanager
def mock_orders_api():
    with patch('odoo.addons.connector_amazon_sp.components.api.amazon.Orders') as mock_orders:
        mock_orders.return_value.get_order.return_value = ApiResponse(**get_order_response)
        mock_orders.return_value.get_order_items.return_value = ApiResponse(**get_order_items_response)
        mock_orders.return_value.get_order_address.return_value = ApiResponse(**get_order_address_response)
        mock_orders.return_value.get_order_buyer_info.return_value = ApiResponse(**get_order_buyer_info_response)
        yield
