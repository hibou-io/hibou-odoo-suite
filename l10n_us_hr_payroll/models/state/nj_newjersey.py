# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def nj_newjersey_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'NJ'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('nj_njw4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    allowances = payslip.contract_id.us_payroll_config_value('nj_njw4_sit_allowances')
    sit_rate_table_key = payslip.contract_id.us_payroll_config_value('nj_njw4_sit_rate_table')
    if not sit_rate_table_key and filing_status in ('single', 'married_joint'):
        sit_rate_table_key = 'A'
    elif not sit_rate_table_key:
        sit_rate_table_key = 'B'
    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    sit_table = payslip.rule_parameter('us_nj_sit_rate')[sit_rate_table_key].get(schedule_pay)
    allowance_value = payslip.rule_parameter('us_nj_sit_allowance_rate')[schedule_pay]
    if not allowances:
        return 0.0, 0.0

    gross_taxable_income = wage - (allowance_value * allowances)
    withholding = 0.0
    prior_wage_base = 0.0
    for row in sit_table:
        wage_base, base_amt, rate = row
        wage_base = float(wage_base)
        rate = rate / 100.0
        if gross_taxable_income <= wage_base:
            withholding = base_amt + ((gross_taxable_income - prior_wage_base) * rate)
            break
        prior_wage_base = wage_base

    withholding += additional
    return wage, -((withholding / wage) * 100.0)
