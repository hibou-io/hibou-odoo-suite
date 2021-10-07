# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def sc_south_carolina_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'SC'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    personal_exempt = payslip.contract_id.us_payroll_config_value('state_income_tax_exempt')
    if personal_exempt:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('sc_w4_sit_allowances')
    tax_rate = payslip.rule_parameter('us_sc_sit_tax_rate')
    personal_exemption = payslip.rule_parameter('us_sc_sit_personal_exemption_rate')
    deduction = payslip.rule_parameter('us_sc_sit_standard_deduction_rate')

    annual_wage = wage * pay_periods
    personal_exemption_amt = allowances * personal_exemption
    standard_deduction = 0.0
    if allowances > 0:
        if (annual_wage * 0.1) > deduction:
            standard_deduction = deduction
        else:
            standard_deduction = annual_wage * (10 / 100)
    taxable_income = annual_wage - personal_exemption_amt - standard_deduction
    withholding = 0.0
    last = 0.0
    for cap, rate, flat_amt in tax_rate:
        if float(cap) > taxable_income:
            withholding = (taxable_income * (rate / 100.0) - flat_amt)
            break
    withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
