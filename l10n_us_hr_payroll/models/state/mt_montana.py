# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def mt_montana_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'MT'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    if payslip.contract_id.us_payroll_config_value('mt_mw4_sit_exempt'):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    exemptions = payslip.contract_id.us_payroll_config_value('mt_mw4_sit_exemptions')
    exemption_rate = payslip.rule_parameter('us_mt_sit_exemption_rate').get(schedule_pay)
    withholding_rate = payslip.rule_parameter('us_mt_sit_rate').get(schedule_pay)
    if not exemption_rate or not withholding_rate:
        return 0.0, 0.0

    adjusted_wage = wage - (exemption_rate * (exemptions or 0))
    withholding = 0.0
    if adjusted_wage > 0.0:
        prior_wage_cap = 0.0
        for row in withholding_rate:
            wage_cap, base, rate = row
            wage_cap = float(wage_cap)  # e.g. 'inf'
            if adjusted_wage < wage_cap:
                withholding = round(base + ((rate / 100.0) * (adjusted_wage - prior_wage_cap)))
                break
            prior_wage_cap = wage_cap
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
