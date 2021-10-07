# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def il_illinois_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'IL'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    basic_allowances_rate = payslip.rule_parameter('us_il_sit_basic_allowances_rate')
    additional_allowances_rate = payslip.rule_parameter('us_il_sit_additional_allowances_rate')
    basic_allowances = payslip.contract_id.us_payroll_config_value('il_w4_sit_basic_allowances')
    additional_allowances = payslip.contract_id.us_payroll_config_value('il_w4_sit_additional_allowances')

    rate = 4.95 / 100.0
    withholding = rate * (wage - (((basic_allowances * basic_allowances_rate) + (additional_allowances *
                                                                                 additional_allowances_rate)) / pay_periods))
    if withholding < 0.0:
        withholding = 0.0
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
