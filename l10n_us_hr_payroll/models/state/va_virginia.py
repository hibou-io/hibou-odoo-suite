# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def va_virginia_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'VA'
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
    personal_exemptions = payslip.contract_id.us_payroll_config_value('va_va4_sit_exemptions')
    other_exemptions = payslip.contract_id.us_payroll_config_value('va_va4_sit_other_exemptions')
    personal_exemption_rate = payslip.rule_parameter('us_va_sit_exemption_rate')
    other_exemption_rate = payslip.rule_parameter('us_va_sit_other_exemption_rate')
    deduction = payslip.rule_parameter('us_va_sit_deduction')
    withholding_rate = payslip.rule_parameter('us_va_sit_rate')

    taxable_wage = (wage * pay_periods) - (deduction + (personal_exemptions * personal_exemption_rate) + (other_exemptions * other_exemption_rate))
    withholding = 0.0
    if taxable_wage > 0.0:
        for row in withholding_rate:
            if taxable_wage > row[0]:
                selected_row = row
        wage_min, base, rate = selected_row
        withholding = base + ((taxable_wage - wage_min) * rate / 100.0)
        withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
