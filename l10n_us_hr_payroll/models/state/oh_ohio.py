# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def oh_ohio_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'OH'
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
    exemptions = payslip.contract_id.us_payroll_config_value('oh_it4_sit_exemptions')
    exemption_rate = payslip.rule_parameter('us_oh_sit_exemption_rate')
    withholding_rate = payslip.rule_parameter('us_oh_sit_rate')
    multiplier_rate = payslip.rule_parameter('us_oh_sit_multiplier')

    taxable_wage = (wage * pay_periods) - (exemption_rate * (exemptions or 0))
    withholding = 0.0
    if taxable_wage > 0.0:
        prior_wage_cap = 0.0
        for row in withholding_rate:
            wage_cap, base, rate = row
            wage_cap = float(wage_cap)  # e.g. 'inf'
            if taxable_wage < wage_cap:
                withholding = base + (rate * (taxable_wage - prior_wage_cap))
                break
            prior_wage_cap = wage_cap
    # Normalize to pay periods
    withholding /= pay_periods
    withholding *= multiplier_rate
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
