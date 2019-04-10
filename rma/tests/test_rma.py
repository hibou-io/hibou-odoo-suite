from odoo.tests import common
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class TestRMA(common.TransactionCase):
    def setUp(self):
        super(TestRMA, self).setUp()
        self.product1 = self.env.ref('product.product_product_24')
        self.template_missing = self.env.ref('rma.template_missing_item')
        self.template_return = self.env.ref('rma.template_picking_return')
        self.partner1 = self.env.ref('base.res_partner_2')

    def test_00_basic_rma(self):
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Should have made pickings
        self.assertEqual(rma.state, 'confirmed')
        # No inbound picking
        self.assertFalse(rma.in_picking_id)
        # Good outbound picking
        self.assertTrue(rma.out_picking_id)
        self.assertEqual(rma_line.product_id, rma.out_picking_id.move_lines.product_id)
        self.assertEqual(rma_line.product_uom_qty, rma.out_picking_id.move_lines.product_uom_qty)

        with self.assertRaises(UserError):
            rma.action_done()

        rma.out_picking_id.move_lines.quantity_done = 2.0
        rma.out_picking_id.action_done()
        rma.action_done()
        self.assertEqual(rma.state, 'done')

    def test_10_rma_cancel(self):
        self.template_missing.usage = False
        rma = self.env['rma.rma'].create({
            'template_id': self.template_missing.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 2.0,
        })
        rma.action_confirm()
        # Good outbound picking
        self.assertEqual(rma.out_picking_id.move_lines.state, 'assigned')
        rma.action_cancel()
        self.assertEqual(rma.out_picking_id.move_lines.state, 'cancel')

    def test_20_picking_rma(self):
        type_out = self.env.ref('stock.picking_type_out')
        location = self.env.ref('stock.stock_location_stock')
        location_customer = self.env.ref('stock.stock_location_customers')
        self.product1.tracking = 'serial'

        # Need to ensure this is the only quant that can be reserved for this move.
        adj = self.env['stock.inventory'].create({
            'name': 'Test',
            'location_id': location.id,
            'filter': 'product',
            'product_id': self.product1.id,
        })
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': 'X100',
            'product_uom_id': self.product1.uom_id.id,
        })
        self.assertFalse(lot.quant_ids)
        self.assertEqual(lot.product_qty, 0.0)

        adj.action_start()
        self.assertTrue(adj.line_ids)
        adj.line_ids.write({
            'product_qty': 0.0,
        })

        self.env['stock.inventory.line'].create({
            'inventory_id': adj.id,
            'location_id': location.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'prod_lot_id': lot.id,
            'product_qty': 1.0,
        })

        adj._action_done()
        self.assertEqual(self.product1.qty_available, 1.0)
        self.assertTrue(lot.quant_ids)
        # Test some internals in Odoo 12.0
        lot_internal_quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
        self.assertEqual(len(lot_internal_quants), 1)
        self.assertEqual(lot_internal_quants.mapped('quantity'), [1.0])
        # Re-compute qty as it does not depend on anything.
        lot._product_qty()
        self.assertEqual(lot.product_qty, 1.0)

        # Create initial picking that will be returned by RMA
        picking_out = self.env['stock.picking'].create({
            'partner_id': self.partner1.id,
            'name': 'testpicking',
            'picking_type_id': type_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        self.env['stock.move'].create({
            'name': self.product1.name,
            'product_id': self.product1.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product1.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
        })
        picking_out.with_context(planned_picking=True).action_confirm()

        # Try to RMA item not delivered yet
        rma = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        self.assertEqual(rma.state, 'draft')
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma.lines), 1)

        # Make sure that we cannot 'return' if we cannot 'reverse' a stock move
        # (this is what `in_require_return` and `out_require_return` do on `rma.template`)
        with self.assertRaises(UserError):
            rma.action_confirm()

        # Finish our original picking
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')

        # The only lot should be reserved, so we shouldn't get an exception finishing the transfer.
        picking_out.move_line_ids.write({
            'qty_done': 1.0,
        })
        picking_out.button_validate()
        self.assertEqual(picking_out.state, 'done')

        # Now we can 'return' that picking
        rma.action_confirm()
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = rma.in_picking_id.move_line_ids[0]
        self.assertTrue(pack_opt)

        # We cannot check this directly anymore.  Instead just try to return the same lot and make sure you can.
        # self.assertEqual(pack_opt.lot_id, lot)

        with self.assertRaises(UserError):
            rma.action_done()

        pack_opt.qty_done = 1.0
        with self.assertRaises(UserError):
            # require a lot
            rma.in_picking_id.button_validate()

        pack_opt.lot_id = lot
        rma.in_picking_id.button_validate()
        rma.action_done()

        # Ensure that the same lot was in fact returned into our destination inventory
        quant = self.env['stock.quant'].search([('product_id', '=', self.product1.id), ('location_id', '=', location.id)])
        self.assertEqual(len(quant), 1)
        self.assertEqual(quant.lot_id, lot)

        # Make another RMA for the same picking
        rma2 = self.env['rma.rma'].create({
            'template_id': self.template_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'stock_picking_id': picking_out.id,
        })
        wizard = self.env['rma.picking.make.lines'].create({
            'rma_id': rma2.id,
        })
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma2.lines), 1)

        rma2.action_confirm()

        # In Odoo 10, this would not have been able to reserve.
        # In Odoo 11, reservation can still happen, but at least we can't move the same lot twice!
        # self.assertEqual(rma2.in_picking_id.state, 'confirmed')

        # Requires Lot
        with self.assertRaises(UserError):
            rma2.in_picking_id.move_line_ids.write({'qty_done': 1.0})
            rma2.in_picking_id.button_validate()

        # Assign existing lot
        rma2.in_picking_id.move_line_ids.write({
            'lot_id': lot.id
        })

        # Existing lot cannot be re-used.
        with self.assertRaises(ValidationError):
            rma2.in_picking_id.action_done()

        # RMA cannot be completed because the inbound picking state is confirmed
        with self.assertRaises(UserError):
            rma2.action_done()
