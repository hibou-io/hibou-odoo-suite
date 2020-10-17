# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ct_connecticut_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'CT'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    withholding_code = payslip.contract_id.us_payroll_config_value('ct_w4na_sit_code')
    exemption_table = payslip.rule_parameter('us_ct_sit_personal_exemption_rate').get(withholding_code, [('inf', 0.0)])
    initial_tax_tbl = payslip.rule_parameter('us_ct_sit_initial_tax_rate').get(withholding_code, [('inf', 0.0, 0.0)])
    tax_table = payslip.rule_parameter('us_ct_sit_tax_rate').get(withholding_code, [('inf', 0.0)])
    recapture_table = payslip.rule_parameter('us_ct_sit_recapture_rate').get(withholding_code, [('inf', 0.0)])
    decimal_table = payslip.rule_parameter('us_ct_sit_decimal_rate').get(withholding_code, [('inf', 0.0)])

    annual_wages = wage * pay_periods
    personal_exemption = 0.0
    for bracket in exemption_table:
        if annual_wages <= float(bracket[0]):
            personal_exemption = bracket[1]
            break

    withholding = 0.0
    taxable_income = annual_wages - personal_exemption
    if taxable_income < 0.0:
        taxable_income = 0.0

    if taxable_income:
        initial_tax = 0.0
        last = 0.0
        for bracket in initial_tax_tbl:
            if taxable_income <= float(bracket[0]):
                initial_tax = bracket[1] + ((bracket[2] / 100.0) * (taxable_income - last))
                break
            last = bracket[0]

        tax_add_back = 0.0
        for bracket in tax_table:
            if annual_wages <= float(bracket[0]):
                tax_add_back = bracket[1]
                break

        recapture_amount = 0.0
        for bracket in recapture_table:
            if annual_wages <= float(bracket[0]):
                recapture_amount = bracket[1]
                break

        withholding = initial_tax + tax_add_back + recapture_amount
        decimal_amount = 1.0
        for bracket in decimal_table:
            if annual_wages <= float(bracket[0]):
                decimal_amount= bracket[1]
                break

        withholding = withholding * (1.00 - decimal_amount)
        if withholding < 0.0:
            withholding = 0.0
        withholding /= pay_periods

    withholding += additional
    return wage, -((withholding / wage) * 100.0)
