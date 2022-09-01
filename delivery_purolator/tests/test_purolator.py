
from odoo.tests.common import Form, TransactionCase


class TestPurolator(TransactionCase):
    def setUp(self):
        super().setUp()
        self.carrier = self.env.ref('delivery_purolator.purolator_ground', raise_if_not_found=False)
        if not self.carrier or not self.carrier.purolator_api_key:
            self.skipTest('Purolator Shipping not configured, skipping tests.')
        if self.carrier.prod_environment:
            self.skipTest('Purolator Shipping configured to use production credentials, skipping tests.')
        
        self.shipper_partner = self.env['res.partner'].create({
            'name': 'Canadian Address',
            'zip': 'L4W5M8',
        })
        self.shipper_warehouse = self.env['stock.warehouse'].create({
            'partner_id': self.shipper_partner.id,
            'name': 'Canadian Warehouse',
            'code': 'CWH',
        })
        self.receiver_partner = self.env['res.partner'].create({
            'name': 'Receiver Address',
            'city': 'Burnaby',
            'state_id': self.ref('base.state_ca_bc'),
            'country_id': self.ref('base.ca'),
            'zip': 'V5C5A9',
        })
        self.storage_box = self.env.ref('product.product_product_6')
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.receiver_partner.id,
            'warehouse_id': self.shipper_warehouse.id,
            'order_line': [(0, 0, {
                'name': self.storage_box.name,
                'product_id': self.storage_box.id,
                'product_uom_qty': 3.0,
                'product_uom': self.storage_box.uom_id.id,
                'price_unit': self.storage_box.lst_price,
            })],
        })
    
    def test_00_rate_order(self):
        # Regular Update Shipping functionality
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
                'default_order_id': self.sale_order.id,
                'default_carrier_id': self.ref('delivery_purolator.purolator_ground'),
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.update_price()
        self.assertGreater(choose_delivery_carrier.delivery_price, 0.0, "Purolator delivery cost for this SO has not been correctly estimated.")
        
        # Multi-rating with sale order
        rates = self.carrier.rate_shipment_multi(order=self.sale_order)
        carrier_express = self.env.ref('delivery_purolator.purolator_ground')
        rate_express = list(filter(lambda r: r['carrier'] == carrier_express, rates))
        rate_express = rate_express and rate_express[0]
        self.assertGreater(rate_express['price'], 0.0)
        self.assertGreater(rate_express['transit_days'], 0)
