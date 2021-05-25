# from datetime import date
# from .common import TestCAPayslip
# import logging
#
# _logger = logging.getLogger("__name__")
#
#
# class TestPayslip(TestCAPayslip):
#     # https://www.canada.ca/en/revenue-agency/services/forms-publications/payroll/t4127-payroll-deductions-formulas/t4127-jan/t4127-jan-payroll-deductions-formulas-computer-programs.html
#
#     # P = The number of pay periods in the year:
#     # Weekly P = 52 (or 53 where applicable)
#     # Biweekly P = 26 (or 27 where applicable)
#     # Semi-monthly P = 24
#     # Monthly P = 12
#     # Other P = 10, 13, 22, or any other number of pay periods for the year
#
#     def test_2021_federal_payslip(self):
#
#         salary = 80000.0
#         annual_pay_periods_p = 12
#
#         # i = Gross remuneration for the pay period.This includes overtime earned and paid in the same pay period,
#         # pension income, qualified pension income, and taxable benefits,
#         # but does not include bonuses, retroactive pay increases, or other non-periodic payments
#
#         # included
#         overtime = 200.0
#         pension_income = 3000.0
#         qualified_pension_income = 2000.0
#         taxable_benefits = 400.0
#
#         # not included
#         bonuses = 50.0
#         retroactive_pay_increase = 45.0
#         nonperiodic_payments = 55.0
#         non_gross_remuneration = bonuses + retroactive_pay_increase + nonperiodic_payments
#
#         gross_remuneration_for_period_i = (salary/annual_pay_periods_p) + overtime + pension_income + qualified_pension_income + taxable_benefits
#
#         # F = Payroll deductions for the pay period for employee contributions to a registered pension plan (RPP) for current and past services, a registered retirement savings plan (RRSP), to a pooled registered pension plan (PRPP), or a retirement compensation arrangement (RCA).For tax deduction purposes, employers can deduct amounts contributed to an RPP, RRSP, PRPP, or RCA by or on behalf of an employee to determine the employee's taxable income
#         rpp = 100.0 #registered pension plan
#         rrsp = 150.0 #registered retirement savings plan
#         prpp = 200.0 #pooled registered pension plan
#         rca = 250.0 #retirement compensation arrangement
#         employee_contribution_deductions_f = rpp + rrsp + prpp + rca
#
#         #F2 = Alimony or maintenance payments required by a legal document dated before May 1, 1997, to be payroll-deducted authorized by a tax services office or tax centre
#         alimony_before_1997_05_01 = 100.0
#         maintenance_payments_before_1997_05_01 = 150.0
#         required_deductions_f2 = alimony_before_1997_05_01 + maintenance_payments_before_1997_05_01
#
#         #U1 = Union dues for the pay period paid to a trade union, an association of public servants, or dues required under the law of a province to a parity or advisory committee or similar body
#         union_dues_u1 = 50.0
#
#         #HD = Annual deduction for living in a prescribed zone, as shown on Form TD1
#         prescribed_zone_hd = 60.0
#
#         #F1 = Annual deductions such as child care expenses and support payments, requested by an employee or pensioner and authorized by a tax services office or tax centre
#         employee_requested_deduction_f1 = 70.0
#
#         #L = Additional tax deductions for the pay period requested by the employee or pensioner as shown on Form TD1
#         additional_ee_deductions_l = 1200.0
#
#         #T = Estimated federal and provincial or territorial tax deductions for the pay period
#         estimated_total_tax = None
#
#         #A = Annual taxable income = [P × (I – F – F2 – U1 )] – HD – F1
#         # If the result is negative, T = L.
#         annual_taxable_income = (
#                 annual_pay_periods_p
#                  *(
#                     gross_remuneration_i
#                     - employee_contribution_deductions_f
#                     - required_deductions_f2
#                     - union_dues_u1
#                    )
#                 - prescribed_zone_hd
#                 - employee_requested_deduction_f1
#         )
#
#         if annual_taxable_income < 0:
#             estimated_total_tax = additional_ee_deductions_l
#
#         employee = self._createEmployee()
#         country_id = self.env['res.country'].search([('code', '=', 'CA')])
#         self.assertEqual(employee.country_id, country_id, 'The employee\'s country_id is not for Canada')
#
#         contract = self._createContract(employee, wage=salary)
#         self.assertEqual(contract.wage, salary, 'The contract salary of "%s" does not equal the test salary of "%s".' % (contract.wage, salary))
#
#         self._log('2021 tax first payslip:')
#         payslip = self._createPayslip(employee, '2021-01-01', '2021-01-31')
#         self.assertEqual(payslip.contract_id, contract)
#
#         #Determine the taxable income for the pay period (pay minus allowable deductions) and multiply it by the number of pay periods in the year to get an estimated annual taxable income amount. This annual taxable income amount is factor A.
#         #assert(gross_remuneration_for_period_i = gross payslip_pay - non_gross_remuneration)
#
#         # Calculate the basic federal tax on the estimated annual taxable income, after allowable federal non-refundable tax credits. The basic federal tax is factor T3.
#         # T3 = Annual basic federal tax
#         # = (R × A) – K – K1 – K2 – K3 – K4
#
#         # (R federal rate for income based on table
#         # X A Annual Income)
#         # - K Federal constant. The constant is the tax overcharged when applying the 20.5%, 26%, 29%, and 33% rates to the annual taxable income A
#         # - K1 Federal non-refundable personal tax credit (the lowest federal tax rate is used to calculate this credit)
#         # - K2 Federal Canada Pension Plan contributions and employment insurance premiums tax credits for the year (the lowest federal tax rate is used to calculate this credit).
#             # Note: If an employee has already contributed the maximum CPP and EI, for the year with the employer, use the maximum CPP and EI deduction to determine the credit for the rest of the year. If, during the pay period in which the employee reaches the maximum, the CPP and  EI, when annualized, is less than the annual maximum, use the maximum annual deduction(s) in that pay period
#         # - K3 Other federal non-refundable tax credits (such as medical expenses and charitable donations) authorized by a tax services office or tax centre
#         # - K4 Factor calculated using the Canada employment amount credit (the lowest federal tax rate is used to calculate this credit)
#         # If the result is negative, T3 = $0.
#
#         # Calculate the annual federal tax payable. This is factor T1.
#
#
#         # Calculate the basic provincial or territorial tax on the estimated annual taxable income, after allowable provincial or territorial personal tax credits. The annual basic provincial or territorial tax is factor T4.
#         # Calculate the annual provincial or territorial tax deduction. This is factor T2.
#         # To get the estimated federal and provincial or territorial tax deductions for a pay period, add the federal and provincial or territorial tax, and divide the result by the number of pay periods. This is factor T.
#
