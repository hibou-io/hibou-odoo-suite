from odoo.tests import common


class TestMaintenanceCharge(common.TransactionCase):
    """Tests for charges
    """

    def test_create(self):
        test_charge = 21.0
        equipment = self.env['maintenance.equipment'].create({
            'name': 'Monitor',
        })

        self.assertFalse(equipment.charge_ids)
        self.env['maintenance.equipment.charge'].create({
            'equipment_id': equipment.id,
            'name': 'test',
            'amount': test_charge,
        })
        self.assertTrue(equipment.charge_ids)
        self.assertAlmostEqual(equipment.charge_ids[0].amount, test_charge)
