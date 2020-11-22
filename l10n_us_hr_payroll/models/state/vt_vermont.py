# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def vt_vermont_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'VT'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    if payslip.contract_id.us_payroll_config_value('state_income_tax_exempt'):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('vt_w4vt_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('vt_w4vt_sit_allowances')
    allowance_amt = payslip.rule_parameter('us_vt_sit_allowances_rate')[schedule_pay]
    tax_table = payslip.rule_parameter('us_vt_sit_tax_rate')[filing_status].get(schedule_pay)

    taxable_income = wage - (allowances * allowance_amt)
    withholding = 0.0
    last = 0.0
    for row in tax_table:
        amt, flat_fee, rate = row
        if wage <= float(amt):
            withholding = ((taxable_income - last) * (rate / 100)) + flat_fee
            break
        last = amt

    withholding = max(withholding, 0.0)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
