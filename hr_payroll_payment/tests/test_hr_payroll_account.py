# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


import odoo.tests
from odoo.addons.hr_payroll_account.tests.test_hr_payroll_account import TestHrPayrollAccount as TestBase

@odoo.tests.tagged('post_install', '-at_install')
class TestHrPayrollAccount(TestBase):

    def setUp(self):
        super().setUp()
        # Two employees, but in stock tests they share the same partner...
        self.hr_employee_mark.address_home_id = self.env['res.partner'].create({
            'name': 'employee_mark',
        })
        # This rule has a partner, and is the only one with any accounting side effects.
        # Remove partner to use the home address...
        rule = self.env.ref('hr_payroll.hr_salary_rule_houserentallowance1')
        rule.partner_id = False

    def test_00_hr_payslip_run(self):
        # Original method groups but has no partners.
        self.account_journal.payroll_entry_type = 'original'
        super().test_00_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 3)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 1)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 0)

    def test_01_hr_payslip_run(self):
        # Grouped method groups but has partners.
        self.account_journal.payroll_entry_type = 'grouped'
        super().test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 3)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 1)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 2)

    def test_01_2_hr_payslip_run(self):
        # Payslip method makes an entry per payslip
        self.account_journal.payroll_entry_type = 'slip'
        # Call 'other' implementation.
        super().test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 3)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 3)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 2)
