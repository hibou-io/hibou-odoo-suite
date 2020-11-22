# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def in_indiana_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'IN'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    personal_exemption = payslip.contract_id.us_payroll_config_value('in_w4_sit_personal_exemption')
    personal_exemption_rate = payslip.rule_parameter('us_in_sit_personal_exemption_rate')[schedule_pay][personal_exemption - 1]
    dependent_exemption = payslip.contract_id.us_payroll_config_value('in_w4_sit_dependent_exemption')
    dependent_exemption_rate = payslip.rule_parameter('us_in_sit_dependent_exemption_rate')[schedule_pay][dependent_exemption - 1]
    income_tax_rate = payslip.rule_parameter('us_in_suta_income_rate')

    taxable_income = wage - (personal_exemption_rate + dependent_exemption_rate)
    withholding = taxable_income * (income_tax_rate / 100.0)

    withholding = max(withholding, 0.0)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
