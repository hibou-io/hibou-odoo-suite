from unittest.mock import patch

from odoo.tests import common
from odoo.exceptions import UserError
from odoo.addons.sale_sourced_by_line.models.sale import SaleOrderLine


def patch_prepare_procurement_values(self):
    vals = super(SaleOrderLine, self)._prepare_procurement_values()
    #don't inject warehouse_id to raise an error
    # vals.update({'warehouse_id': self.warehouse_id or self.order_id.warehouse_id})
    if self.date_planned:
        vals.update({'date_planned': self.date_planned})
    elif self.order_id.date_planned:
        vals.update({'date_planned': self.order_id.date_planned})
    return vals


class TestSaleSources(common.TransactionCase):

    def setUp(self):
        super(TestSaleSources, self).setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.product_1 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test Product 1',
            'is_storable': True,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'consu',
            'name': 'Test Product 2',
            'is_storable': True,
        })
        self.wh_1 = self.env.ref('stock.warehouse0')
        self.wh_2 = self.env['stock.warehouse'].create({
            'name': 'Test WH2',
            'code': 'TWH2',
        })

    def test_plan_one_warehouse(self):
        so = self.env['sale.order'].create({
            'warehouse_id': self.wh_1.id,
            'partner_id': self.partner.id,
            'date_planned': '2018-01-01',
            'order_line': [(0, 0, {
                'product_id': self.product_1.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product_1.uom_id.id,
                'price_unit': 10.0,
            }),
                           (0, 0, {
                               'product_id': self.product_2.id,
                               'product_uom_qty': 1.0,
                               'product_uom': self.product_2.uom_id.id,
                               'price_unit': 10.0,
                           })]
        })

        # check and error raise if warehouse is not filled on sol
        with patch.object(SaleOrderLine, '_prepare_procurement_values', patch_prepare_procurement_values):
            with self.assertRaises(UserError):
                so.action_confirm()

        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(len(so.picking_ids), 1)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == self.wh_1)), 1)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == self.wh_2)), 0)

    def test_plan_two_warehouses(self):
        so = self.env['sale.order'].create({
            'warehouse_id': self.wh_1.id,
            'partner_id': self.partner.id,
            'date_planned': '2018-01-01',
            'order_line': [(0, 0, {'product_id': self.product_1.id}),
                           (0, 0, {'product_id': self.product_2.id,
                                   'date_planned': '2018-02-01', 'warehouse_id': self.wh_2.id})]
        })
        # in 13 default computation, this would result in a failure
        self.assertTrue(so.order_line.filtered(lambda l: l.warehouse_id))
        so.action_confirm()
        self.assertTrue(so.state in ('sale', 'done'))
        self.assertEqual(len(so.picking_ids), 2)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == self.wh_1)), 1)
        self.assertEqual(len(so.picking_ids.filtered(lambda p: p.picking_type_id.warehouse_id == self.wh_2)), 1)
