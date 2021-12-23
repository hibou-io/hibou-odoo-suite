# # Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.
#
# def _compute_employee_contribution_deductions(payslip):
#     # todo: _compute_employee_contribution_deductions
#     return 0.0
#
# def _compute_annual_taxable_income(payslip):
#     # A = Annual taxable income = [P × (I – F – F2 – U1 )] – HD – F1
#     #         # If the result is negative, T = L.
#     #         annual_taxable_income = (
#     #                 annual_pay_periods_p
#     #                  *(
#     #                     gross_remuneration_i
#     #                     - employee_contribution_deductions_f
#     #                     - required_deductions_f2
#     #                     - union_dues_u1
#     #                    )
#     #                 - prescribed_zone_hd
#     #                 - employee_requested_deduction_f1
#     #         )
#     pay_periods = payslip.dict.get_pay_periods_in_year()
#     annual_pay_periods_p = pay_periods[payslip.contract_id.schedule_pay]
#     gross_remuneration_i = annual_pay_periods_p * payslip.contract_id.wage
#     employee_contribution_deductions_f = _compute_employee_contribution_deductions(payslip)
#     required_deductions_f2 = _compute_employee_contribution_deductions(payslip)
#     pass