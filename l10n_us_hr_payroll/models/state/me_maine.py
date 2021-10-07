# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def me_maine_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """

    state_code = 'ME'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('me_w4me_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    exempt = payslip.contract_id.us_payroll_config_value('state_income_tax_exempt')
    if exempt:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('me_w4me_sit_allowances')
    tax_rate = payslip.rule_parameter('us_me_sit_tax_rate')[filing_status]
    personal_exemption = payslip.rule_parameter('us_me_sit_personal_exemption_rate')
    standard_deduction = payslip.rule_parameter('us_me_sit_standard_deduction_rate')[filing_status]

    taxable_income = wage * pay_periods
    exemption_amt = allowances * personal_exemption
    last = 0.0
    standard_deduction_amt = 0.0

    for row in standard_deduction:  #Standard_deduction is a set so looping through without giving it order isn't working
        amt, flat_amt = row
        if taxable_income < 82900:
            standard_deduction_amt = flat_amt
            break
        elif taxable_income < amt:
            standard_deduction_amt = last * (amt - taxable_income) / flat_amt
            break
        last = flat_amt
    annual_income = taxable_income - (exemption_amt + standard_deduction_amt)
    withholding = 0.0
    for row in tax_rate:
        amt, flat_fee, rate = row
        if annual_income < float(amt):
            withholding = ((annual_income - last) * (rate / 100)) + flat_fee
            break
        last = amt

    withholding = max(withholding, 0.0)
    withholding = round(withholding / pay_periods)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
