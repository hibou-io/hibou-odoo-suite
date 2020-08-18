# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def nd_north_dakota_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'ND'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('nd_w4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowance = payslip.contract_id.us_payroll_config_value('nd_w4_sit_allowances')
    allowance_rate = payslip.rule_parameter('us_nd_sit_allowances_rate')[schedule_pay]
    tax_rate = payslip.rule_parameter('us_nd_sit_tax_rate')[filing_status].get(schedule_pay)

    taxable_income = wage - (allowance * allowance_rate)
    withholding = 0.0
    last = 0.0
    for row in tax_rate:
        amt, flat_fee, rate = row
        if taxable_income < float(amt):
            withholding = ((taxable_income - last) * (rate / 100)) + flat_fee
            break
        last = amt

    withholding = round(withholding)
    withholding = max(withholding, 0.0)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
