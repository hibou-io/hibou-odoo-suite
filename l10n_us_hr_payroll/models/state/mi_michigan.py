# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies


def mi_michigan_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'MI'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    if payslip.dict.contract_id.us_payroll_config_value('state_income_tax_exempt'):
        return 0.0, 0.0

    # Determine Wage
    wage = categories.GROSS + categories.DED_FIT_EXEMPT
    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.dict.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    exemption_rate = payslip.dict.rule_parameter('us_mi_sit_exemption_rate')
    exemption = payslip.dict.contract_id.us_payroll_config_value('mi_w4_sit_exemptions')

    if wage == 0.0:
        return 0.0, 0.0

    annual_exemption = (exemption * exemption_rate) / pay_periods
    withholding = ((wage - annual_exemption) * 0.0425)
    if withholding < 0.0:
        withholding = 0.0
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
