# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def hi_hawaii_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'HI'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('hi_hw4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    allowances = payslip.contract_id.us_payroll_config_value('hi_hw4_sit_allowances')
    tax_table = payslip.rule_parameter('us_hi_sit_tax_rate')[filing_status]
    personal_exemption = payslip.rule_parameter('us_hi_sit_personal_exemption_rate')

    taxable_income = (wage * pay_periods) - (personal_exemption * allowances)
    withholding = 0.0
    last = 0.0
    for row in tax_table:
        if taxable_income <= float(row[0]):
            withholding = row[1] + ((row[2] / 100.0) * (taxable_income - last))
            break
        last = row[0]

    withholding = max(withholding, 0.0)
    withholding = withholding / pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
