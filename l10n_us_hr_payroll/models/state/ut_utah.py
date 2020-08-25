# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ut_utah_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'UT'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.dict.contract_id.us_payroll_config_value('ut_w4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.dict.contract_id.schedule_pay
    additional = payslip.dict.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    tax_rate = payslip.dict.rule_parameter('us_ut_tax_rate')
    allowances = payslip.dict.rule_parameter('us_ut_sit_allowances_rate')[filing_status].get(schedule_pay)
    tax_table = payslip.dict.rule_parameter('us_ut_sit_tax_rate')[filing_status].get(schedule_pay)

    taxable_income = wage * tax_rate
    withholding = 0.0
    amt, rate = tax_table
    withholding = taxable_income - (allowances - ((wage - amt) * (rate / 100)))

    withholding = max(withholding, 0.0)
    withholding += additional
    withholding = round(withholding)
    return wage, -((withholding / wage) * 100.0)
