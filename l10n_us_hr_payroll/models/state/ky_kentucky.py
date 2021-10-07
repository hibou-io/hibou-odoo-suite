# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ky_kentucky_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'KY'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    tax_rate = payslip.rule_parameter('us_ky_sit_tax_rate')
    standard_deduction = payslip.rule_parameter('us_ky_sit_standard_deduction_rate')

    taxable_income = (wage * pay_periods) - standard_deduction
    withholding = taxable_income * (tax_rate / 100)

    withholding = max(withholding, 0.0)
    withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
