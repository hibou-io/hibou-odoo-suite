from odoo.addons.hr_payroll.tests.common import TestPayslipBase
from odoo.tests.common import Form
from datetime import date


class TestPayslipYtd(TestPayslipBase):
    def test_00_payslip_ytd(self):
        # The common test leaves the contract in draft mode
        richard_contract = self.richard_emp.contract_ids[0]
        richard_contract.state = 'open'
        # pay structure in TestPayslipBase is missing default Salary Rules
        # I don't need all of them, but I would like to use Basic Salary
        self.developer_pay_structure.write({
            'rule_ids': [(4, self.env['hr.salary.rule'].search([('code', '=', 'BASIC')], limit=1).id)]
        })

        payslip_form = Form(self.env['hr.payslip'])
        payslip_form.employee_id = self.richard_emp
        payslip_form.date_from = date(2020, 1, 1)
        payslip_form.date_to = date(2020, 1, 31)
        richard_payslip = payslip_form.save()

        richard_payslip.compute_sheet()
        richard_payslip.action_payslip_done()
        richard_payslip.flush()  # Didn't have to do this in 12, but now the test fails if I don't

        basic_line = richard_payslip.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(basic_line.amount, 5000.0)
        self.assertEqual(basic_line.total, 5000.0)
        ytd = richard_payslip.ytd(basic_line.code, allow_draft=False)
        self.assertEqual(ytd, {'total': 5000.0, 'quantity': 1.0, 'amount': 5000.0})

        # get worked days
        self.assertTrue(richard_payslip.worked_days_line_ids)
        worked_day_line = richard_payslip.worked_days_line_ids.filtered(lambda l: l.code == 'WORK100')
        self.assertEqual(worked_day_line.amount, 5000.0)
        worked_day_ytd = richard_payslip.worked_ytd(worked_day_line.code, allow_draft=False)
        self.assertEqual(worked_day_ytd, {'amount': 5000.0})

        payslip_form = Form(self.env['hr.payslip'])
        payslip_form.employee_id = self.richard_emp
        payslip_form.date_from = date(2020, 2, 1)
        payslip_form.date_to = date(2020, 2, 29)
        richard_payslip_next = payslip_form.save()
        richard_payslip_next.compute_sheet()
        richard_payslip_next.flush()

        basic_line = richard_payslip_next.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(basic_line.amount, 5000.0)
        self.assertEqual(basic_line.total, 5000.0)
        ytd = richard_payslip_next.ytd(basic_line.code, allow_draft=True)
        self.assertEqual(ytd, {'total': 10000.0, 'quantity': 2.0, 'amount': 10000.0})
        ytd = richard_payslip_next.ytd(basic_line.code, allow_draft=False)
        self.assertEqual(ytd, {'total': 5000.0, 'quantity': 1.0, 'amount': 5000.0})
