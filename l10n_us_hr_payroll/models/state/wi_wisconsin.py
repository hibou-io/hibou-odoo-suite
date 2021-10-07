# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def wi_wisconsin_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'WI'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    if payslip.contract_id.us_payroll_config_value('state_income_tax_exempt'):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('wi_wt4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    exemptions = payslip.contract_id.us_payroll_config_value('wi_wt4_sit_exemptions')
    exemption_amt = payslip.rule_parameter('us_wi_sit_exemption_rate')
    tax_table = payslip.rule_parameter('us_wi_sit_tax_rate')[filing_status]

    taxable_income = wage * pay_periods
    withholding = 0.0
    last = 0.0
    for row in tax_table:
        amt, rate, flat_fee = row
        if taxable_income <= float(amt):
            withholding = (((taxable_income - last) * (rate / 100)) + flat_fee) - (exemptions * exemption_amt)
            break
        last = amt

    withholding = max(withholding, 0.0)
    withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
