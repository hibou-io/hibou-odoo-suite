from odoo.fields import Command
from odoo.addons.sale_margin.tests.test_sale_margin import TestSaleMargin
from datetime import datetime


class TestInvoiceMargin(TestSaleMargin):

    def setUp(self):
        super(TestInvoiceMargin, self).setUp()
        self.AccountMove = self.env['account.move']
        self.SaleOrder = self.env['sale.order']

    def test_invoice_margin(self):
        self.product.standard_price = 700.0
        order = self.empty_order

        order.order_line = [
            Command.create({
                'price_unit': 1000.0,
                'product_uom_qty': 10.0,
                'product_id': self.product.id,
            }),
        ]
        # Confirm the sales order.
        order.action_confirm()
        # Verify that margin field gets bind with the value.
        self.assertEqual(order.margin, 3000.00, "Sales order profit should be 6000.00")
        self.assertEqual(order.margin_percent, 0.3, "Sales order margin should be 30%")

        order.order_line.write({'qty_delivered': 10.0})

        # Invoice the sales order.
        inv = order._create_invoices()
        self.assertEqual(inv.margin, order.margin)
        self.assertEqual(inv.margin_percent, order.margin_percent)

        account = self.env['account.account'].search([('account_type', '=', 'expense')], limit=1)
        self.assertTrue(account)
        inv = self.AccountMove.create({
            'move_type': 'in_invoice',
            'partner_id': order.partner_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'name': '[CARD] Graphics Card',
                    'price_unit': 1000.0,
                    'purchase_price': 600.0,
                    'quantity': 10.0,
                    'product_id': self.product.id}),
                (0, 0, {
                    'account_id': account.id,
                    'name': 'Line without product_uom',
                    'price_unit': 1000.0,
                    'purchase_price': 800.0,
                    'quantity': 10.0,})
                ],
        })
        self.assertEqual(len(inv.invoice_line_ids), 2)
        self.assertEqual(inv.margin, 6000.0)
        self.assertEqual(inv.margin_percent, 0.3)
