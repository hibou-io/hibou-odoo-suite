from odoo.tests import common


class TestMaintenanceUsage(common.TransactionCase):
    """Tests for usage on creation and update
    """

    def test_create(self):
        test_usage = 21.0
        equipment = self.env['maintenance.equipment'].create({
            'name': 'Monitor',
            'usage_qty': test_usage,
        })

        self.assertTrue(equipment.usage_log_ids)
        self.assertEqual(equipment.usage_log_ids[0].qty, test_usage)

    def test_update(self):
        test_usage = 21.0
        test_usage2 = 50.1
        equipment = self.env['maintenance.equipment'].create({
            'name': 'Monitor',
            'usage_qty': test_usage,
        })
        equipment.usage_qty = test_usage2
        updated_usage = equipment.usage_log_ids.filtered(lambda u: abs(u.qty - test_usage2) < 0.01)

        self.assertTrue(updated_usage)
        self.assertAlmostEqual(updated_usage[0].qty, test_usage2)

    def test_maintenance_usage(self):
        test_usage = 21.0
        test_usage2 = 50.1
        equipment = self.env['maintenance.equipment'].create({
            'name': 'Monitor',
            'usage_qty': test_usage,
            'maintenance_usage': 20.0,
            'maintenance_team_id': self.env['maintenance.team'].search([], limit=1).id
        })
        self.assertFalse(equipment.maintenance_ids)

        equipment.usage_qty = test_usage2
        self.assertTrue(equipment.maintenance_ids)
