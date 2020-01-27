from odoo.tests import common


class TestMaintenanceRepair(common.TransactionCase):
    """Tests for repairs
    """

    def test_create(self):
        equipment = self.env['maintenance.equipment'].create({
            'name': 'Monitor',
        })

        loc_from = self.env.ref('stock.stock_location_stock')
        loc_to = self.env.ref('stock.stock_location_output')
        request = self.env['maintenance.request'].create({
            'name': 'Repair Monitor',
            'equipment_id': equipment.id,
            'repair_location_id': loc_from.id,
            'repair_location_dest_id': loc_to.id,
        })
        self.assertEqual(request.repair_status, 'no')

        product_to_repair = self.env.ref('product.product_product_24_product_template').product_variant_id
        line = self.env['maintenance.request.repair.line'].create({
            'request_id': request.id,
            'product_id': product_to_repair.id,
            'product_uom_id': product_to_repair.uom_id.id,
        })

        self.assertEqual(request.repair_status, 'to repair')
        line.action_complete()
        self.assertEqual(request.repair_status, 'repaired')
        self.assertEqual(line.state, 'done')
        self.assertTrue(line.move_id, 'Expect a stock move to be done.')



