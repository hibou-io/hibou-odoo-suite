# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common


class TestStockException(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))

    def test_delivery_order_exception(self):
        exception = self.env.ref('stock_exception.excep_no_zip')
        exception.active = True
        partner = self.env.ref('base.res_partner_12')  # Azure Interior
        partner.zip = False
        p = self.env.ref('product.product_product_6')
        stock_location = self.env.ref('stock.stock_location_stock')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.env['stock.quant']._update_available_quantity(p, stock_location, 100)
        delivery_order = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': self.ref('stock.picking_type_out'),
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_line_ids': [(0, 0, {'product_id': p.id,
                                      'product_uom_id': p.uom_id.id,
                                      'qty_done': 3.0,
                                      'location_id': stock_location.id,
                                      'location_dest_id': customer_location.id})],
        })

        # validate delivery order
        delivery_order.button_validate()
        self.assertEqual(delivery_order.state, 'draft')

        # Simulation the opening of the wizard sale_exception_confirm and
        # set ignore_exception to True
        stock_exception_confirm = self.env['stock.exception.confirm'].with_context(
            {
                'active_id': delivery_order.id,
                'active_ids': [delivery_order.id],
                'active_model': delivery_order._name
            }).create({'ignore': True})
        stock_exception_confirm.action_confirm()
        self.assertTrue(delivery_order.ignore_exception)
        self.assertEqual(delivery_order.state, 'done')
