from odoo import fields
from .common import TestCAPayslip
import logging

_logger = logging.getLogger("__name__")


class TestPayslip(TestCAPayslip):

    def test_basic_federal_tax(self,
                               salary=7000.0,
                               date_from='2021-01-01',
                               date_to='2021-01-31',
                               state_code=None,
                               **extra_contract):
        annual_pay_periods_p = 12
        employee = self._createEmployee()
        contract = self._createCAContract(employee=employee)


        self._log('2021 tax first payslip:')
        payslip = self._createPayslip(employee, date_from, date_to)
        # self.assertEqual(payslip.struct_type_id, )
        self.assertEqual(payslip.contract_id, contract, f'Payslip contract {str(payslip.contract_id)} is not correct')
        self.assertEqual(payslip.struct_id.name, 'Canada Employee Standard',
                         f'payroll structure {payslip.struct_id.name} is not correct')
        self.assertEqual(payslip.date_from, fields.Date.from_string(date_from),
                         f'payslip date_from {payslip.date_from} is not correct ')
        self.assertEqual(payslip.date_to, fields.Date.from_string(date_to),
                         f'payslip date_to {payslip.date_to} is not correct ')
        self.assertEqual(payslip.employee_id.name, 'Jared',
                         f'payslip employee {payslip.employee_id.name} is not correct')

        _logger.warning(str(payslip.read()))
        for line in payslip.line_ids:
            _logger.warning(f'payslip line read {str(line)}************************************')
            _logger.warning(line.read())

            # if line.name == 'EE: CA Federal Income Tax':
            #     _logger.warning(f'payslip line read {str(line)}************************************')
            #     _logger.warning(line.read())
        # _logger.warning('payslip.contract_id************************************')
        # _logger.warning(str(payslip.contract_id.read()))
        # _logger.warning('payslip.contract_id.structure_type_id.read()************************************')
        # _logger.warning(str(payslip.contract_id.structure_type_id.read()))
        # _logger.warning('payslip.contract_id.structure_type_id.struct_ids[0].read()************************************')
        # _logger.warning(str(payslip.contract_id.structure_type_id.struct_ids[0].read()))
        # _logger.warning('payslip.contract_id.structure_type_id.struct_ids[0].rule_ids[0].read()************************************')
        # _logger.warning(str(payslip.contract_id.structure_type_id.struct_ids[0].rule_ids[0].read()))
        # _logger.warning('payslip.rule_parameter(rule_parameter_ca_fed_tax_rate)************************************')

        self.assertPayrollAlmostEqual(payslip.net_wage, 5565)
        # self.assertEqual(payslip.net_wage, 5565, 'total tax is off')

        # schedule_pay = payslip.contract_id.schedule_pay
        # additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
        # sit_allowances = payslip.contract_id.us_payroll_config_value('ca_de4_sit_allowances')
        # additional_allowances = payslip.contract_id.us_payroll_config_value('ca_de4_sit_additional_allowances')
        # low_income_exemption = payslip.rule_parameter('us_ca_sit_income_exemption_rate')[schedule_pay]
        # estimated_deduction = payslip.rule_parameter('us_ca_sit_estimated_deduction_rate')[schedule_pay]
        # tax_table = payslip.rule_parameter('us_ca_sit_tax_rate')[filing_status].get(schedule_pay)
        # standard_deduction = payslip.rule_parameter('us_ca_sit_standard_deduction_rate')[schedule_pay]
        # exemption_allowances = payslip.rule_parameter('us_ca_sit_exemption_allowance_rate')[schedule_pay]

        #Determine the taxable income for the pay period (pay minus allowable deductions) and multiply it by the number of pay periods in the year to get an estimated annual taxable income amount. This annual taxable income amount is factor A.
        #assert(gross_remuneration_for_period_i = gross payslip_pay - non_gross_remuneration)

        # Calculate the basic federal tax on the estimated annual taxable income, after allowable federal non-refundable tax credits. The basic federal tax is factor T3.
        # T3 = Annual basic federal tax
        # = (R × A) – K – K1 – K2 – K3 – K4

        # (R federal rate for income based on table
        # X A Annual Income)
        # - K2 Federal Canada Pension Plan contributions and employment insurance premiums tax credits for the year (the lowest federal tax rate is used to calculate this credit).
            # Note: If an employee has already contributed the maximum CPP and EI, for the year with the employer, use the maximum CPP and EI deduction to determine the credit for the rest of the year. If, during the pay period in which the employee reaches the maximum, the CPP and  EI, when annualized, is less than the annual maximum, use the maximum annual deduction(s) in that pay period
        # - K3 Other federal non-refundable tax credits (such as medical expenses and charitable donations) authorized by a tax services office or tax centre
        # - K4 Factor calculated using the Canada employment amount credit (the lowest federal tax rate is used to calculate this credit)
        # - K Federal constant. The constant is the tax overcharged when applying the 20.5%, 26%, 29%, and 33% rates to the annual taxable income A
        # - K1 Federal non-refundable personal tax credit (the lowest federal tax rate is used to calculate this credit)

        # If the result is negative, T3 = $0.

        # Calculate the annual federal tax payable. This is factor T1.


        # Calculate the basic provincial or territorial tax on the estimated annual taxable income, after allowable provincial or territorial personal tax credits. The annual basic provincial or territorial tax is factor T4.
        # Calculate the annual provincial or territorial tax deduction. This is factor T2.
        # To get the estimated federal and provincial or territorial tax deductions for a pay period, add the federal and provincial or territorial tax, and divide the result by the number of pay periods. This is factor T.

    # test_federal_with