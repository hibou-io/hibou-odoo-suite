# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ia_iowa_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'IA'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    if payslip.contract_id.us_payroll_config_value('state_income_tax_exempt'):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    fed_withholding = categories.EE_US_941_FIT
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('ia_w4_sit_allowances')
    standard_deduction = payslip.rule_parameter('us_ia_sit_standard_deduction_rate')[schedule_pay]
    tax_table = payslip.rule_parameter('us_ia_sit_tax_rate')[schedule_pay]
    deduction_per_allowance = payslip.rule_parameter('us_ia_sit_deduction_allowance_rate')[schedule_pay]

    t1 = wage + fed_withholding
    standard_deduction_amt = standard_deduction[0] if allowances < 2 else standard_deduction[1]
    t2 = t1 - standard_deduction_amt
    t3 = 0.0
    last = 0.0
    for row in tax_table:
        cap, rate, flat_fee = row
        if float(cap) > float(t2):
            taxed_amount = t2 - last
            t3 = flat_fee + (rate * taxed_amount)
            break
        last = cap
    withholding = t3 - (deduction_per_allowance * allowances)

    withholding = max(withholding, 0.0)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
