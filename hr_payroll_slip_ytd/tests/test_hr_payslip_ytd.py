from odoo.addons.hr_payroll.tests.common import TestPayslipBase


class TestPayslipYtd(TestPayslipBase):
    def test_00_payslip_ytd(self):
        richard_payslip = self.env['hr.payslip'].create({
            'name': 'Payslip of Richard',
            'employee_id': self.richard_emp.id,
            'contract_id': self.richard_emp.contract_id.id,
        })

        richard_payslip.compute_sheet()
        richard_payslip.action_payslip_done()
        basic_line = richard_payslip.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(basic_line.amount, 5000.0)
        ytd = richard_payslip.ytd('BASIC', allow_draft=False)
        self.assertEqual(ytd, {'total': 5000.0, 'quantity': 1.0, 'amount': 5000.0})

        richard_payslip_next = self.env['hr.payslip'].create({
            'name': 'Payslip of Richard',
            'employee_id': self.richard_emp.id,
            'contract_id': self.richard_emp.contract_id.id,
        })

        richard_payslip_next.compute_sheet()
        basic_line = richard_payslip_next.line_ids.filtered(lambda l: l.code == 'BASIC')
        self.assertEqual(basic_line.amount, 5000.0)
        ytd = richard_payslip_next.ytd('BASIC', allow_draft=True)
        self.assertEqual(ytd, {'total': 10000.0, 'quantity': 2.0, 'amount': 10000.0})
        ytd = richard_payslip_next.ytd('BASIC', allow_draft=False)
        self.assertEqual(ytd, {'total': 5000.0, 'quantity': 1.0, 'amount': 5000.0})
