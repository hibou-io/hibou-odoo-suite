# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ga_georgia_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'GA'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0
    ga_filing_status = payslip.contract_id.us_payroll_config_value('ga_g4_sit_filing_status')
    if not ga_filing_status:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    dependent_allowances = payslip.contract_id.us_payroll_config_value('ga_g4_sit_dependent_allowances')
    additional_allowances = payslip.contract_id.us_payroll_config_value('ga_g4_sit_additional_allowances')
    dependent_allowance_rate = payslip.rule_parameter('us_ga_sit_dependent_allowance_rate').get(schedule_pay)
    personal_allowance = payslip.rule_parameter('us_ga_sit_personal_allowance').get(ga_filing_status, {}).get(schedule_pay)
    deduction = payslip.rule_parameter('us_ga_sit_deduction').get(ga_filing_status, {}).get(schedule_pay)
    withholding_rate = payslip.rule_parameter('us_ga_sit_rate').get(ga_filing_status, {}).get(schedule_pay)
    if not all((dependent_allowance_rate, personal_allowance, deduction, withholding_rate)):
        return 0.0, 0.0

    after_standard_deduction = wage - deduction
    allowances = dependent_allowances + additional_allowances
    working_wages = after_standard_deduction - (personal_allowance + (allowances * dependent_allowance_rate))

    withholding = 0.0
    if working_wages > 0.0:
        prior_row_base = 0.0
        for row in withholding_rate:
            wage_base, base, rate = row
            wage_base = float(wage_base)
            if working_wages < wage_base:
                withholding = base + ((working_wages - prior_row_base) * rate / 100.0)
                break
            prior_row_base = wage_base

    withholding += additional
    return wage, -((withholding / wage) * 100.0)
