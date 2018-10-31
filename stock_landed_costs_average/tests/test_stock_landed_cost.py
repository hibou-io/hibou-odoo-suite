from odoo.addons.stock_landed_costs.tests.test_stock_landed_costs_purchase import TestLandedCosts


class TestLandedCostsAverage(TestLandedCosts):

    def setUp(self):
        super(TestLandedCostsAverage, self).setUp()
        self.product_refrigerator.cost_method = 'average'
        self.product_oven.cost_method = 'average'

    def test_00_landed_costs_on_incoming_shipment(self):
        original_standard_price = self.product_refrigerator.standard_price
        super(TestLandedCostsAverage, self).test_00_landed_costs_on_incoming_shipment()
        self.assertTrue(original_standard_price != self.product_refrigerator.standard_price)

    def test_01_landed_costs_simple_average(self):
        self.assertEqual(self.product_refrigerator.standard_price, 1.0)
        self.assertEqual(self.product_refrigerator.qty_available, 0.0)
        picking_in = self.Picking.create({
            'partner_id': self.supplier_id,
            'picking_type_id': self.picking_type_in_id,
            'location_id': self.supplier_location_id,
            'location_dest_id': self.stock_location_id})
        self.Move.create({
            'name': self.product_refrigerator.name,
            'product_id': self.product_refrigerator.id,
            'product_uom_qty': 5,
            'product_uom': self.product_refrigerator.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location_id,
            'location_dest_id': self.stock_location_id})
        picking_in.action_confirm()
        res_dict = picking_in.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()
        self.assertEqual(self.product_refrigerator.standard_price, 1.0)
        self.assertEqual(self.product_refrigerator.qty_available, 5.0)

        stock_landed_cost = self._create_landed_costs({
            'equal_price_unit': 50,
            'quantity_price_unit': 0,
            'weight_price_unit': 0,
            'volume_price_unit': 0}, picking_in)
        stock_landed_cost.compute_landed_cost()
        stock_landed_cost.button_validate()
        account_entry = self.env['account.move.line'].read_group(
            [('move_id', '=', stock_landed_cost.account_move_id.id)], ['debit', 'credit', 'move_id'], ['move_id'])[0]
        self.assertEqual(account_entry['debit'], 50.0, 'Wrong Account Entry')
        self.assertEqual(self.product_refrigerator.standard_price, 11.0)

    def test_02_landed_costs_average(self):
        self.assertEqual(self.product_refrigerator.standard_price, 1.0)
        self.assertEqual(self.product_refrigerator.qty_available, 0.0)
        picking_in = self.Picking.create({
            'partner_id': self.supplier_id,
            'picking_type_id': self.picking_type_in_id,
            'location_id': self.supplier_location_id,
            'location_dest_id': self.stock_location_id})
        self.Move.create({
            'name': self.product_refrigerator.name,
            'product_id': self.product_refrigerator.id,
            'product_uom_qty': 5,
            'product_uom': self.product_refrigerator.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location_id,
            'location_dest_id': self.stock_location_id})
        picking_in.action_confirm()
        res_dict = picking_in.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()
        self.assertEqual(self.product_refrigerator.standard_price, 1.0)
        self.assertEqual(self.product_refrigerator.qty_available, 5.0)

        picking_out = self.Picking.create({
            'partner_id': self.customer_id,
            'picking_type_id': self.picking_type_out_id,
            'location_id': self.stock_location_id,
            'location_dest_id': self.customer_location_id})
        self.Move.create({
            'name': self.product_refrigerator.name,
            'product_id': self.product_refrigerator.id,
            'product_uom_qty': 2,
            'product_uom': self.product_refrigerator.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location_id,
            'location_dest_id': self.customer_location_id})
        picking_out.action_confirm()
        picking_out.action_assign()
        res_dict = picking_out.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()
        self.assertEqual(self.product_refrigerator.standard_price, 1.0)
        self.assertEqual(self.product_refrigerator.qty_available, 3.0)

        stock_landed_cost = self._create_landed_costs({
            'equal_price_unit': 50,
            'quantity_price_unit': 0,
            'weight_price_unit': 0,
            'volume_price_unit': 0}, picking_in)
        stock_landed_cost.compute_landed_cost()
        stock_landed_cost.button_validate()
        self.assertEqual(self.product_refrigerator.standard_price, 11.0)
