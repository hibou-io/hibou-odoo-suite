# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def de_delaware_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'DE'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('de_w4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    tax_table = payslip.rule_parameter('us_de_sit_tax_rate')
    personal_exemption = payslip.rule_parameter('us_de_sit_personal_exemption_rate')
    allowances = payslip.contract_id.us_payroll_config_value('de_w4_sit_dependent')
    standard_deduction = payslip.rule_parameter('us_de_sit_standard_deduction_rate')

    taxable_income = wage * pay_periods
    if filing_status == 'single':
        taxable_income -= standard_deduction
    else:
        taxable_income -= standard_deduction * 2

    withholding = 0.0
    last = 0.0
    for row in tax_table:
        if taxable_income <= float(row[0]):
            withholding = (row[1] + ((row[2] / 100.0) * (taxable_income - last)) - (allowances * personal_exemption))
            break
        last = row[0]

    withholding = max(withholding, 0.0)
    withholding = withholding / pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
