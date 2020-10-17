# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ar_arkansas_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'AR'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    if payslip.contract_id.us_payroll_config_value('state_income_tax_exempt'):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    sit_tax_rate = payslip.rule_parameter('us_ar_sit_tax_rate')
    standard_deduction = payslip.rule_parameter('us_ar_sit_standard_deduction_rate')
    allowances = payslip.contract_id.us_payroll_config_value('ar_ar4ec_sit_allowances')

    allowances_amt = allowances * 26.0
    taxable_income = (wage * pay_periods) - standard_deduction
    if taxable_income < 87001.0:
        taxable_income = (taxable_income // 50) * 50.0 + 50.0

    withholding = 0.0
    for row in sit_tax_rate:
        cap, rate, adjust_amount = row
        cap = float(cap)
        if cap > taxable_income:
            withholding = (((rate / 100.0) * taxable_income) - adjust_amount) - allowances_amt
            break

    # In case withholding or taxable_income is negative
    withholding = max(withholding, 0.0)
    withholding = round(withholding / pay_periods)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
