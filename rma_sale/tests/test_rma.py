from odoo.addons.rma.tests.test_rma import TestRMA
from odoo.exceptions import UserError


class TestRMASale(TestRMA):

    def setUp(self):
        super(TestRMASale, self).setUp()
        self.template2 = self.env.ref('rma_sale.template_sale_return')

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
            'template_id': self.template2.id,
            'partner_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'sale_order_id': order.id,
        })
        self.assertEqual(rma.state, 'draft')
        rma_line = self.env['rma.line'].create({
            'rma_id': rma.id,
            'product_id': self.product1.id,
            'product_uom_id': self.product1.uom_id.id,
            'product_uom_qty': 1.0,
        })
        with self.assertRaises(UserError):
            rma.action_confirm()

        order.picking_ids.force_assign()
        pack_opt = self.env['stock.pack.operation'].search([('picking_id', '=', order.picking_ids.id)], limit=1)
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': 'X100',
        })
        self.env['stock.pack.operation.lot'].create({'operation_id': pack_opt.id, 'lot_id': lot.id, 'qty': 1.0})
        pack_opt.qty_done = 1.0
        order.picking_ids.do_transfer()
        self.assertEqual(order.picking_ids.state, 'done')

        # Confirm RMA
        rma.action_confirm()
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = self.env['stock.pack.operation'].search([('picking_id', '=', rma.in_picking_id.id)], limit=1)
        self.assertEqual(pack_opt.pack_lot_ids.lot_id, lot)

        with self.assertRaises(UserError):
            rma.action_done()

        pack_opt.pack_lot_ids.qty = 1.0
        pack_opt.qty_done = 1.0
        rma.in_picking_id.do_transfer()
        rma.action_done()
