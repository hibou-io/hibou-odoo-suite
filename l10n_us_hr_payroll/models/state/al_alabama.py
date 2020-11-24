# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def al_alabama_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'AL'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    exemptions = payslip.contract_id.us_payroll_config_value('al_a4_sit_exemptions')
    if not exemptions:
        return 0.0, 0.0

    personal_exempt = payslip.contract_id.us_payroll_config_value('state_income_tax_exempt')
    if personal_exempt:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    tax_table = payslip.rule_parameter('us_al_sit_tax_rate')
    dependent_rate = payslip.rule_parameter('us_al_sit_dependent_rate')
    standard_deduction = payslip.rule_parameter('us_al_sit_standard_deduction_rate').get(exemptions, 0.0)
    personal_exemption = payslip.rule_parameter('us_al_sit_personal_exemption_rate').get(exemptions, 0.0)
    dependent = payslip.contract_id.us_payroll_config_value('al_a4_sit_dependents')
    fed_withholding = categories.EE_US_941_FIT

    annual_wage = wage * pay_periods
    standard_deduction_amt = 0.0
    personal_exemption_amt = 0.0
    dependent_amt = 0.0
    withholding = 0.0

    if standard_deduction:
        row = standard_deduction
        last_amt = 0.0
        for data in row:
            if annual_wage < float(data[0]):
                if len(data) > 3:
                    increment_count = (- (wage - last_amt) // data[3])
                    standard_deduction_amt = data[1] - (increment_count * data[2])
                else:
                    standard_deduction_amt = data[1]
            else:
                last_amt = data[0]
    after_deduction = annual_wage - standard_deduction_amt
    after_fed_withholding = (fed_withholding * pay_periods) + after_deduction
    if not personal_exempt:
        personal_exemption_amt = personal_exemption
    after_personal_exemption = after_fed_withholding - personal_exemption_amt
    for row in dependent_rate:
        if annual_wage < float(row[1]):
            dependent_amt = row[0] * dependent
            break

    taxable_amount = after_personal_exemption - dependent_amt
    last = 0.0
    tax_table = tax_table['M'] if exemptions == 'M' else tax_table['0']
    for row in tax_table:
        if taxable_amount < float(row[0]):
            withholding = withholding + ((taxable_amount - last) * (row[1] / 100))
            break
        withholding = withholding + ((row[0] - last) * (row[1] / 100))
        last = row[0]

    if withholding < 0.0:
        withholding = 0.0
    withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
