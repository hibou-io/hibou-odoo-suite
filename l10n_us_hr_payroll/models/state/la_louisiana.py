# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def la_louisiana_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'LA'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('la_l4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    personal_exemptions = payslip.contract_id.us_payroll_config_value('la_l4_sit_exemptions')
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    dependent_exemptions = payslip.contract_id.us_payroll_config_value('la_l4_sit_dependents')
    tax_table = payslip.rule_parameter('us_la_sit_tax_rate')[filing_status]
    exemption_rate = payslip.rule_parameter('us_la_sit_personal_exemption_rate')
    dependent_rate = payslip.rule_parameter('us_la_sit_dependent_rate')

    annual_wage = wage * pay_periods
    
    effect_cap, multiplier = tax_table[0]

    after_credits_under = (2.100 / 100) * (((personal_exemptions * exemption_rate) +
                                           (dependent_exemptions * dependent_rate)) / pay_periods)
    after_credits_over = 0.00
    if after_credits_under > effect_cap:
        after_credits_under = effect_cap
        after_credits_over_check = ((personal_exemptions * exemption_rate) + (dependent_exemptions * dependent_rate)) - effect_cap
        after_credits_over = (multiplier / 100.00) * (after_credits_over_check / pay_periods) if after_credits_over_check > 0 else 0.00
    withholding = 0.0
    last = 0.0
    for amt, rate in tax_table:
        withholding = withholding + ((rate / 100.0) * (wage - (last / pay_periods)))
        if annual_wage <= float(amt):
            break
        last = amt

    withholding = withholding - (after_credits_under + after_credits_over)
    withholding = round(withholding, 2)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
