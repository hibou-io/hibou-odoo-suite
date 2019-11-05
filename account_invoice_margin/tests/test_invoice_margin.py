from odoo.addons.sale_margin.tests.test_sale_margin import TestSaleMargin
from datetime import datetime


class TestInvoiceMargin(TestSaleMargin):

    def setUp(self):
        super(TestInvoiceMargin, self).setUp()
        self.AccountMove = self.env['account.move']

    def test_invoice_margin(self):
        """ Test the sale_margin module in Odoo. """
        # Create a sales order for product Graphics Card.
        sale_order_so11 = self.SaleOrder.create({
            'date_order': datetime.today(),
            'name': 'Test_SO011',
            'order_line': [
                (0, 0, {
                    'name': '[CARD] Individual Workplace',
                    'purchase_price': 700.0,
                    'price_unit': 1000.0,
                    'product_uom': self.product_uom_id,
                    'product_uom_qty': 10.0,
                    'state': 'draft',
                    'product_id': self.product_id}),
                (0, 0, {
                    'name': 'Line without product_uom',
                    'price_unit': 1000.0,
                    'purchase_price': 700.0,
                    'product_uom_qty': 10.0,
                    'state': 'draft',
                    'product_id': self.product_id})],
            'partner_id': self.partner_id,
            'partner_invoice_id': self.partner_invoice_address_id,
            'partner_shipping_id': self.partner_invoice_address_id,
            'pricelist_id': self.pricelist_id})
        # Confirm the sales order.
        sale_order_so11.action_confirm()
        # Verify that margin field gets bind with the value.
        self.assertEqual(sale_order_so11.margin, 6000.00, "Sales order margin should be 6000.00")

        sale_order_so11.order_line.write({'qty_delivered': 10.0})

        # Invoice the sales order.
        inv = sale_order_so11._create_invoices()
        self.assertEqual(inv.margin, sale_order_so11.margin)

        account = self.env['account.account'].search([('internal_type', '=', 'other')], limit=1)
        inv = self.AccountMove.create({
            'type': 'in_invoice',
            'partner_id': self.partner_id,
            'invoice_line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'name': '[CARD] Graphics Card',
                    'purchase_price': 600.0,
                    'price_unit': 1000.0,
                    'quantity': 10.0,
                    'product_id': self.product_id}),
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
