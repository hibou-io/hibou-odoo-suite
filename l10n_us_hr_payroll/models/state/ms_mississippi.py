# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ms_mississippi_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'MS'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('ms_89_350_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    exemptions = payslip.contract_id.us_payroll_config_value('ms_89_350_sit_exemption_value')
    standard_deduction = payslip.rule_parameter('us_ms_sit_deduction').get(filing_status)
    withholding_rate = payslip.rule_parameter('us_ms_sit_rate')

    wage_annual = wage * pay_periods
    taxable_income = wage_annual - (exemptions + standard_deduction)
    if taxable_income <= 0.01:
        return wage, 0.0

    withholding = 0.0
    for row in withholding_rate:
        wage_base, base, rate = row
        if taxable_income >= wage_base:
            withholding = base + ((taxable_income - wage_base) * rate)
            break
    withholding /= pay_periods
    withholding = round(withholding)
    withholding += round(additional)
    return wage, -((withholding / wage) * 100.0)
