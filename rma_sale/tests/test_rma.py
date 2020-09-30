# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.addons.rma.tests.test_rma import TestRMA
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class TestRMASale(TestRMA):

    def setUp(self):
        super(TestRMASale, self).setUp()
        self.template_sale_return = self.env.ref('rma_sale.template_sale_return')
        # Make it possible to "see all sale orders", but not be a manager (as managers can RMA ineligible lines)
        self.user1.groups_id += self.env.ref('sales_team.group_sale_salesman_all_leads')

    def test_20_sale_return(self):
        self.template_sale_return.write({
            'usage': 'sale_order',
            'invoice_done': True,
        })
        self.product1.write({
            'type': 'product',
            'invoice_policy': 'delivery',
            'tracking': 'serial',
        })
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
        # Do not allow return.
        self.product1.rma_sale_validity = -1
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0

        with self.assertRaises(UserError):
            wizard.add_lines()

        # Allows returns, but not forever
        self.product1.rma_sale_validity = 5
        original_date_order = order.date_order
        order.write({'date_order': original_date_order - timedelta(days=6)})
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0
        with self.assertRaises(UserError):
            wizard.add_lines()

        # Allows returns due to date
        order.write({'date_order': original_date_order})
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
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
            'company_id': self.env.user.company_id.id,
        })
        pack_opt.qty_done = 1.0
        pack_opt.lot_id = lot
        order.picking_ids.button_validate()
        self.assertEqual(order.picking_ids.state, 'done')

        # Invoice order so that the return is invoicable
        wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids).create({})
        wiz.create_invoices()
        # Odoo 13 Not flushing the order here will cause delivered_qty to be incorrect later
        order.flush()
        self.assertTrue(order.invoice_ids, 'Order did not create an invoice.')

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
        self.assertEqual(rma.in_picking_id.move_lines.sale_line_id, order.order_line)
        self.assertEqual(rma.in_picking_id.state, 'done')
        for move in order.order_line.mapped('move_ids'):
            # Additional testing like this may not be needed in the future.  Was added troubleshooting new 13 ORM
            self.assertEqual(move.state, 'done', 'Move not done ' + str(move.name))
        self.assertEqual(order.order_line.qty_delivered, 0.0)
        rma.action_done()
        self.assertEqual(order.order_line.qty_delivered, 0.0)

        # Finishing the RMA should have made an invoice
        self.assertTrue(rma.invoice_ids, 'Finishing RMA did not create an invoice(s).')

        # Test Ordered Qty was decremented.
        self.assertEqual(order.order_line.product_uom_qty, 0.0)
        self.assertEqual(order.order_line.qty_delivered, 0.0)

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

        self.assertTrue(rma2.in_picking_id.move_line_ids)
        self.assertFalse(rma2.in_picking_id.move_line_ids.lot_id.name)

        # Assign existing lot
        rma2.in_picking_id.move_line_ids.write({
            'lot_id': lot.id,
            'qty_done': 1.0,
        })

        # Existing lot cannot be re-used.
        with self.assertRaises(ValidationError):
            rma2.in_picking_id.action_done()
        
        # RMA cannot be completed because the inbound picking state is confirmed
        with self.assertRaises(UserError):
            rma2.action_done()

    def test_30_product_sale_return_warranty(self):
        self.template_sale_return.write({
            'usage': 'sale_order',
            'invoice_done': True,
            'sale_order_warranty': True,
            'in_to_refund': True,
            'so_decrement_order_qty': False,  # invoice on decremented delivered not decremented order
            'next_rma_template_id': self.template_rtv.id,
        })

        validity = 100  # eligible for 100 days
        warranty_validity = validity + 100  # eligible for 200 days

        self.product1.write({
            'rma_sale_validity': validity,
            'rma_sale_warranty_validity': warranty_validity,
            'type': 'product',
            'invoice_policy': 'delivery',
            'tracking': 'serial',
            'standard_price': 1.5,
        })

        order = self.env['sale.order'].create({
            'partner_id': self.partner1.id,
            'partner_invoice_id': self.partner1.id,
            'partner_shipping_id': self.partner1.id,
            'user_id': self.user1.id,
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
        # Do not allow warranty return.
        self.product1.rma_sale_warranty_validity = -1
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0

        with self.assertRaises(UserError):
            wizard.add_lines()

        # Allows returns, but not forever
        self.product1.rma_sale_warranty_validity = warranty_validity
        original_date_order = order.date_order
        order.write({'date_order': original_date_order - timedelta(days=warranty_validity+1)})
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0
        with self.assertRaises(UserError):
            wizard.add_lines()

        # Allows returns due to date, due to warranty option
        order.write({'date_order': original_date_order - timedelta(days=validity+1)})
        wizard = self.env['rma.sale.make.lines'].with_user(self.user1).create({'rma_id': rma.id})
        self.assertEqual(wizard.line_ids.qty_delivered, 0.0)
        wizard.line_ids.product_uom_qty = 1.0
        wizard.add_lines()

        # finish outbound so that we can invoice.
        order.picking_ids.action_assign()
        pack_opt = order.picking_ids.move_line_ids[0]
        lot = self.env['stock.production.lot'].create({
            'product_id': self.product1.id,
            'name': 'X100',
            'product_uom_id': self.product1.uom_id.id,
            'company_id': self.env.user.company_id.id,
        })
        pack_opt.qty_done = 1.0
        pack_opt.lot_id = lot
        order.picking_ids.button_validate()
        self.assertEqual(order.picking_ids.state, 'done')
        self.assertEqual(order.order_line.qty_delivered, 1.0)

        # Invoice the order so that only the core product is invoiced at the end...
        self.assertFalse(order.invoice_ids)
        wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=order.ids).create({})
        wiz.create_invoices()
        order.flush()
        self.assertTrue(order.invoice_ids)
        order_invoice = order.invoice_ids

        self.assertEqual(rma.lines.product_id, self.product1)
        rma.action_confirm()
        self.assertTrue(rma.in_picking_id)
        self.assertEqual(rma.in_picking_id.state, 'assigned')
        pack_opt = rma.in_picking_id.move_line_ids[0]
        pack_opt.lot_id = lot.id
        pack_opt.qty_done = 1.0
        rma.in_picking_id.button_validate()
        self.assertEqual(rma.in_picking_id.state, 'done')
        order.flush()
        # self.assertEqual(order.order_line.qty_delivered, 0.0)
        rma.action_done()
        self.assertEqual(rma.state, 'done')
        order.flush()

        rma_invoice = rma.invoice_ids
        self.assertTrue(rma_invoice)
        sale_line = rma_invoice.invoice_line_ids.filtered(lambda l: l.sale_line_ids)
        so_line = sale_line.sale_line_ids
        self.assertTrue(sale_line)
        self.assertEqual(sale_line.price_unit, so_line.price_unit)

        # Invoices do not have their anglo-saxon cost lines until they post
        order_invoice.post()
        rma_invoice.post()

        # Find the return to vendor RMA
        rtv_rma = self.env['rma.rma'].search([('parent_id', '=', rma.id)])
        self.assertTrue(rtv_rma)
        self.assertFalse(rtv_rma.out_picking_id)

        wiz = self.env['rma.make.rtv'].with_context(active_model='rma.rma', active_ids=rtv_rma.ids).create({})
        self.assertTrue(wiz.rma_line_ids)
        wiz.partner_id = self.partner2
        wiz.create_batch()
        self.assertTrue(rtv_rma.out_picking_id)
        self.assertEqual(rtv_rma.out_picking_id.partner_id, self.partner2)
