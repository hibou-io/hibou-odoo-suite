# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo.tests import common


class TestCommission(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.user = self.browse_ref('base.user_demo')
        self.employee = self.browse_ref('hr.employee_qdp')  # This is the employee associated with above user.

    def _createUser(self):
        return self.env['res.users'].create({
            'name': 'Coach',
            'email': 'coach',
        })

    def _createEmployee(self, user):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared',
            'address_home_id': user.partner_id.id,
            'user_id': user.id,
        })

    def _createContract(self, employee, commission_rate, admin_commission_rate=0.0):
        other_contracts = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
        if other_contracts:
            # couldn't get the demo contract to not be used if it is
            # installed e.g. by payroll...
            # tried, state->cancel + employee.invalidate_cache() etc.
            other_contracts.unlink()
        return self.env['hr.contract'].create({
            'date_start': '2016-01-01',
            'date_end': '2030-12-31',
            'name': 'Contract for tests',
            'wage': 1000.0,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': employee.id,
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'commission_rate': commission_rate,
            'admin_commission_rate': admin_commission_rate,
            'state': 'open',  # if not "Running" then no automatic selection when Payslip is created in 11.0
        })

    def test_commission(self):
        # find and configure company commissions journal
        commission_journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        self.assertTrue(commission_journal)
        expense_account = self.env.ref('l10n_generic_coa.1_conf_a_expense')
        commission_journal.default_debit_account_id = expense_account
        commission_journal.default_credit_account_id = expense_account
        self.env.user.company_id.commission_journal_id = commission_journal

        coach = self._createEmployee(self.browse_ref('base.user_root'))
        coach_contract = self._createContract(coach, 12.0, admin_commission_rate=2.0)
        user = self.user
        emp = self.employee
        emp.address_home_id = user.partner_id  # Important field for payables.
        emp.coach_id = coach

        contract = self._createContract(emp, 5.0)

        so = self.env['sale.order'].search([('invoice_status', '=', 'to invoice'), ('user_id', '=', user.id)], limit=1)
        self.assertEqual(len(so), 1)

        inv = self.env['account.invoice'].browse(so.action_invoice_create())
        self.assertFalse(inv.commission_ids, 'Commissions exist when invoice is created.')
        inv.action_invoice_open()  # validate
        self.assertEqual(inv.state, 'open')
        self.assertTrue(inv.commission_ids, 'Commissions not created when invoice is validated.')
        self.assertTrue(inv.amount_for_commission())

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == emp.id)
        self.assertEqual(len(user_commission), 1, 'Incorrect commission count %d (expect 1)' % len(user_commission))
        self.assertTrue(user_commission.rate)
        self.assertTrue(user_commission.amount)
        self.assertEqual(user_commission.state, 'draft', 'Commission is not draft.')
        self.assertFalse(user_commission.move_id, 'Commission has existing journal entry.')

        # Amounts
        commission_rate = contract.commission_rate
        self.assertEqual(commission_rate, 5.0)
        expected = (inv.amount_for_commission() * commission_rate) / 100.0
        actual = user_commission.amount
        self.assertAlmostEqual(actual, expected, int(inv.company_currency_id.rounding))

        # Pay.
        inv.pay_and_reconcile(self.env['account.journal'].search([('type', '=', 'bank')], limit=1))
        self.assertEqual(inv.state, 'paid', 'Invoice is not paid.')

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == emp.id)
        self.assertEqual(user_commission.state, 'done', 'Commission is not done.')
        self.assertTrue(user_commission.move_id, 'Commission didn\'t create a journal entry.')
        inv.company_currency_id.rounding

        # Coach/Admin commissions
        coach_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == coach.id)
        self.assertEqual(len(coach_commission), 1, 'Incorrect commission count %d (expect 1)' % len(coach_commission))

        commission_rate = coach_contract.admin_commission_rate
        expected = (inv.amount_for_commission() * commission_rate) / 100.0
        actual = coach_commission.amount
        self.assertAlmostEqual(
            actual,
            expected,
            int(inv.company_currency_id.rounding))

        # Use the "Mark Paid" button
        result_action = user_commission.action_mark_paid()
        self.assertEqual(user_commission.state, 'paid')
        self.assertTrue(user_commission.payment_id)

    def test_commission_on_invoice(self):
        # Set to be On Invoice instead of On Invoice Paid
        self.env.user.company_id.commission_type = 'on_invoice'

        # find and configure company commissions journal
        commission_journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        self.assertTrue(commission_journal)
        expense_account = self.env.ref('l10n_generic_coa.1_conf_a_expense')
        commission_journal.default_debit_account_id = expense_account
        commission_journal.default_credit_account_id = expense_account
        self.env.user.company_id.commission_journal_id = commission_journal


        coach = self._createEmployee(self.browse_ref('base.user_root'))
        coach_contract = self._createContract(coach, 12.0, admin_commission_rate=2.0)
        user = self.browse_ref('base.user_demo')
        emp = self.browse_ref('hr.employee_qdp')  # This is the employee associated with above user.
        emp.address_home_id = user.partner_id  # Important field for payables.
        emp.coach_id = coach

        contract = self._createContract(emp, 5.0)

        so = self.env['sale.order'].search([('invoice_status', '=', 'to invoice'), ('user_id', '=', user.id)], limit=1)
        self.assertEqual(len(so), 1)

        inv = self.env['account.invoice'].browse(so.action_invoice_create())
        self.assertFalse(inv.commission_ids, 'Commissions exist when invoice is created.')
        inv.action_invoice_open()  # validate
        self.assertEqual(inv.state, 'open')
        self.assertTrue(inv.commission_ids, 'Commissions not created when invoice is validated.')

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == emp.id)
        self.assertEqual(len(user_commission), 1, 'Incorrect commission count %d (expect 1)' % len(user_commission))
        self.assertEqual(user_commission.state, 'done', 'Commission is not done.')
        self.assertTrue(user_commission.move_id, 'Commission missing journal entry.')

        # Use the "Mark Paid" button
        user_commission.action_mark_paid()
        self.assertEqual(user_commission.state, 'paid')

    def test_commission_structure(self):
        # Set to be On Invoice instead of On Invoice Paid
        self.env.user.company_id.commission_type = 'on_invoice'

        # find and configure company commissions journal
        commission_journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        self.assertTrue(commission_journal)
        expense_account = self.env.ref('l10n_generic_coa.1_conf_a_expense')
        commission_journal.default_debit_account_id = expense_account
        commission_journal.default_credit_account_id = expense_account
        self.env.user.company_id.commission_journal_id = commission_journal


        coach = self._createEmployee(self.browse_ref('base.user_root'))
        coach_contract = self._createContract(coach, 12.0, admin_commission_rate=2.0)
        user = self.browse_ref('base.user_demo')
        emp = self.browse_ref('hr.employee_qdp')  # This is the employee associated with above user.
        emp.address_home_id = user.partner_id  # Important field for payables.
        emp.coach_id = coach

        contract = self._createContract(emp, 5.0)

        so = self.env['sale.order'].search([('invoice_status', '=', 'to invoice'), ('user_id', '=', user.id)], limit=1)
        self.assertEqual(len(so), 1)

        # Create and set commission structure
        commission_structure = self.env['hr.commission.structure'].create({
            'name': 'Test Structure',
            'line_ids': [
                (0, 0, {'employee_id': emp.id, 'rate': 13.0}),
                (0, 0, {'employee_id': coach.id, 'rate': 0.0}),  # This means it will use the coach's contract normal rate
            ],
        })
        so.partner_id.commission_structure_id = commission_structure

        inv = self.env['account.invoice'].browse(so.action_invoice_create())
        self.assertFalse(inv.commission_ids, 'Commissions exist when invoice is created.')
        inv.action_invoice_open()  # validate
        self.assertEqual(inv.state, 'open')
        self.assertTrue(inv.commission_ids, 'Commissions not created when invoice is validated.')

        user_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == emp.id)
        self.assertEqual(len(user_commission), 1, 'Incorrect commission count %d (expect 1)' % len(user_commission))
        self.assertEqual(user_commission.state, 'done', 'Commission is not done.')
        self.assertEqual(user_commission.rate, 13.0)

        coach_commission = inv.commission_ids.filtered(lambda c: c.employee_id.id == coach.id)
        self.assertEqual(len(coach_commission), 1, 'Incorrect commission count %d (expect 1)' % len(coach_commission))
        self.assertEqual(coach_commission.state, 'done', 'Commission is not done.')
        self.assertEqual(coach_commission.rate, 12.0, 'Commission rate should be the contract rate.')
