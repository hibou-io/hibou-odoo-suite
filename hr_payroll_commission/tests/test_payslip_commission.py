# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta

from odoo.addons.hr_commission.tests import test_commission


class TestCommissionPayslip(test_commission.TestCommission):

    def test_commission(self):
        super().test_commission()
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input')
        payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=14),
        })
        payslip._onchange_employee()
        self.assertFalse(payslip.commission_payment_ids)

        # find unpaid commission payments from super().test_commission()
        commission_payments = self.env['hr.commission.payment'].search([
            ('employee_id', '=', self.employee.id),
        ])
        self.assertTrue(commission_payments)

        # press the button to pay it via payroll
        commission_payments.action_report_in_next_payslip()

        payslip._onchange_employee()
        # has attached commission payments
        self.assertTrue(payslip.commission_payment_ids)
        commission_input_lines = payslip.input_line_ids.filtered(lambda l: l.input_type_id == commission_type)
        self.assertTrue(commission_input_lines)
        self.assertEqual(sum(commission_input_lines.mapped('amount')),
                         sum(commission_payments.mapped('commission_amount')))
