# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def mi_michigan_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'MI'
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
    exemption_rate = payslip.rule_parameter('us_mi_sit_exemption_rate')
    exemption = payslip.contract_id.us_payroll_config_value('mi_w4_sit_exemptions')

    annual_exemption = (exemption * exemption_rate) / pay_periods
    withholding = ((wage - annual_exemption) * 0.0425)
    if withholding < 0.0:
        withholding = 0.0
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
