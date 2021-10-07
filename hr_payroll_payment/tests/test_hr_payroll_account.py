# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


import odoo.tests
from odoo.addons.hr_payroll_account.tests.test_hr_payroll_account import TestHrPayrollAccount as TestBase


@odoo.tests.tagged('post_install', '-at_install')
class TestHrPayrollAccount(TestBase):

    def setUp(self):
        super().setUp()
        # upstream code no-longer sets the journal, though it does create it....
        self.hr_structure_softwaredeveloper.journal_id = self.account_journal
        # upstream code no-longer has any accounts (just makes journal entries without any lines)
        demo_account = self.env.ref('hr_payroll_account.demo_account')
        self.hr_structure_softwaredeveloper.rule_ids.filtered(lambda r: r.code == 'HRA').account_debit = demo_account
        # Need a default account as there will be adjustment lines equal and opposite to the above PT rule...
        self.account_journal.default_account_id = demo_account

        # Two employees, but in stock tests they share the same partner...
        self.hr_employee_mark.address_home_id = self.env['res.partner'].create({
            'name': 'employee_mark',
        })

        # This rule has a partner, and is the only one with any accounting side effects.
        # Remove partner to use the home address...
        self.rule = self.hr_structure_softwaredeveloper.rule_ids.filtered(lambda r: r.code == 'HRA')
        self.rule.partner_id = False

        # configure journal to be able to make payments
        ap = self.hr_employee_mark.address_home_id.property_account_payable_id
        self.assertTrue(ap)
        # note there is no NET rule, so I just use a random allowance with fixed 800.0 amount
        net_rule = self.hr_structure_softwaredeveloper.rule_ids.filtered(lambda r: r.code == 'CA')
        self.assertTrue(net_rule)
        net_rule.account_credit = ap
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        self.account_journal.payroll_payment_journal_id = bank_journal
        self.account_journal.payroll_payment_method_id = bank_journal.outbound_payment_method_line_ids[0].payment_method_id

    def _setup_fiscal_position(self):
        account_rule_debit = self.rule.account_debit
        self.assertTrue(account_rule_debit)
        account_other = self.env['account.account'].search([('id', '!=', account_rule_debit.id)], limit=1)
        self.assertTrue(account_other)
        fp = self.env['account.fiscal.position'].create({
            'name': 'Salary Remap 1',
            'account_ids': [(0, 0, {
                'account_src_id': account_rule_debit.id,
                'account_dest_id': account_other.id,
            })]
        })
        self.hr_contract_john.payroll_fiscal_position_id = fp

    def _setup_fiscal_position_empty(self):
        self._setup_fiscal_position()
        self.hr_contract_john.payroll_fiscal_position_id.write({'account_ids': [(5, 0, 0)]})

    def test_00_hr_payslip_run(self):
        # Original method groups but has no partners.
        self.account_journal.payroll_entry_type = 'original'
        super().test_00_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 2)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 1)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 0)

    def test_00_fiscal_position(self):
        self._setup_fiscal_position()
        self.test_00_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 3)

    def test_00_fiscal_position_empty(self):
        self._setup_fiscal_position_empty()
        self.test_00_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 2)

    def test_01_hr_payslip_run(self):
        # Grouped method groups but has partners.
        self.account_journal.payroll_entry_type = 'grouped'
        super().test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 2)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 1)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 2)
        # what is going on with the 3rd one?!
        slips_to_pay = self.payslip_run.slip_ids
        action = slips_to_pay.action_register_payment()
        payment_ids = action['res_ids']
        self.assertEqual(len(payment_ids), 2)

    def test_01_fiscal_position(self):
        self._setup_fiscal_position()
        self.test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 3)

    def test_01_fiscal_position_empty(self):
        self._setup_fiscal_position_empty()
        self.test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 2)

    def test_01_2_hr_payslip_run(self):
        # Payslip method makes an entry per payslip
        self.account_journal.payroll_entry_type = 'slip'
        # Call 'other' implementation.
        super().test_01_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids), 2)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id')), 2)
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.partner_id')), 2)
        slips_to_pay = self.payslip_run.slip_ids
        # what is going on with the 3rd one?!
        # it is possible to filter it out, but it doesn't change it
        self.assertEqual(len(slips_to_pay), 2)
        action = slips_to_pay.action_register_payment()
        payment_ids = action['res_ids']
        self.assertEqual(len(payment_ids), 2)

    def test_01_2_fiscal_position(self):
        self._setup_fiscal_position()
        self.test_01_2_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 3)

    def test_01_2_fiscal_position_empty(self):
        self._setup_fiscal_position_empty()
        self.test_01_2_hr_payslip_run()
        self.assertEqual(len(self.payslip_run.slip_ids.mapped('move_id.line_ids.account_id')), 2)
