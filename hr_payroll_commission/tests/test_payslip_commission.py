# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date, timedelta

from odoo.addons.hr_commission.tests import test_commission


class TestCommissionPayslip(test_commission.TestCommission):

    def _createContract(self, employee, commission_rate, admin_commission_rate=0.0):
        return self.env['hr.contract'].create({
            'date_start': '2016-01-01',
            'date_end': '2030-12-31',
            'name': 'Contract for tests',
            'wage': 1000.0,
            'wage_type': 'monthly',
            # 'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'structure_type_id': self.ref('hr_contract.structure_type_worker'),
            'employee_id': employee.id,
            'resource_calendar_id': self.ref('resource.resource_calendar_std'),
            'commission_rate': commission_rate,
            'admin_commission_rate': admin_commission_rate,
            'state': 'open',  # if not "Running" then no automatic selection when Payslip is created in 11.0
        })

    def test_commission(self):
        super().test_commission()
        commission_type = self.env.ref('hr_payroll_commission.commission_other_input')
        payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=14),
        })
        self.assertFalse(payslip.commission_payment_ids)
        payslip.action_payslip_cancel()

        # find unpaid commission payments from super().test_commission()
        commission_payments = self.env['hr.commission.payment'].search([
            ('employee_id', '=', self.employee.id),
        ])
        self.assertTrue(commission_payments)

        # press the button to pay it via payroll
        commission_payments.action_report_in_next_payslip()

        payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=14),
        })
        # has attached commission payments
        self.assertTrue(payslip.commission_payment_ids)
        commission_input_lines = payslip.input_line_ids.filtered(lambda l: l.input_type_id == commission_type)
        self.assertTrue(commission_input_lines)
        self.assertEqual(sum(commission_input_lines.mapped('amount')),
                         sum(commission_payments.mapped('commission_amount')))
