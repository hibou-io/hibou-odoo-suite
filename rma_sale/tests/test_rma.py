from odoo.addons.rma.tests.test_rma import TestRMA
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class TestRMASale(TestRMA):

    def setUp(self):
        super(TestRMASale, self).setUp()
        self.template_sale_return = self.env.ref('rma_sale.template_sale_return')

    def test_20_sale_return(self):
        self.product1.tracking = 'serial'
        order = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product1.uom_id.id,
                'price_unit': 10.0,
            })]
        })
        order.action_confirm()
        self.assertTrue(order.state in ('sale', 'done'))
        self.assertEqual(len(order.picking_ids), 1, 'Tests only run with single stage delivery.')

        # Try to RMA item not delivered yet
        rma = self.env['rma.rma'].create({
            'template_id': self.template_sale_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'sale_order_id': order.id,
        })
        self.assertEqual(rma.state, 'draft')
        wizard = self.env['rma.sale.make.lines'].create({
            'rma_id': rma.id,
        })
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma.lines), 1)
        with self.assertRaises(UserError):
            rma.action_confirm()

        order.picking_ids.action_assign()
        pack_opt = order.picking_ids.move_line_ids[0]
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': 'X100',
            'product_uom_id': self.product1.uom_id.id,
        })
        pack_opt.qty_done = 1.0
        pack_opt.lot_id = lot
        order.picking_ids.button_validate()
        self.assertEqual(order.picking_ids.state, 'done')
        wizard = self.env['rma.sale.make.lines'].create({
            'rma_id': rma.id,
        })
        self.assertEqual(wizard.line_ids.qty_delivered, 1.0)

        # Confirm RMA
        rma.action_confirm()
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = rma.in_picking_id.move_line_ids[0]

        with self.assertRaises(UserError):
            rma.action_done()

        pack_opt.lot_id = lot
        pack_opt.qty_done = 1.0
        rma.in_picking_id.button_validate()
        rma.action_done()

        # Test Ordered Qty was decremented.
        self.assertEqual(order.order_line.product_uom_qty, 0.0)

        # Make another RMA for the same sale order
        rma2 = self.env['rma.rma'].create({
            'template_id': self.template_sale_return.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'sale_order_id': order.id,
        })
        wizard = self.env['rma.sale.make.lines'].create({
            'rma_id': rma2.id,
        })
        # The First completed RMA will have "un-delivered" it for invoicing purposes.
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()
        self.assertEqual(len(rma2.lines), 1)

        rma2.action_confirm()

        # In Odoo 10, this would not have been able to reserve.
        # In Odoo 11, reservation can still happen, but at least we can't move the same lot twice!
        #self.assertEqual(rma2.in_picking_id.state, 'confirmed')

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
