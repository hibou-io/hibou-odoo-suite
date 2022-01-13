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
    # deduction_table introduced in 2022
    deduction_table = payslip.rule_parameter('us_wi_sit_deduction_rate')
    if deduction_table:
        deduction_table = deduction_table[filing_status]
    # tax_table simplified in 2022
    tax_table = payslip.rule_parameter('us_wi_sit_tax_rate')
    if isinstance(tax_table, dict):
        tax_table = tax_table[filing_status]

    taxable_income = wage * pay_periods  # (a)
    if deduction_table:
        deduction = 0.0
        last_wage_cap = 0.0
        last_deduction = 0.0
        last_rate = 0.0
        for row in deduction_table:
            wage_cap, deduction, rate = row
            if taxable_income <= wage_cap:
                if last_rate:
                    deduction = last_deduction - ((taxable_income - last_wage_cap) * last_rate / 100.0)
                break
            last_wage_cap, last_deduction, last_rate = row
        taxable_income -= deduction  # (b)
    
    taxable_income -= exemption_amt * exemptions  # (c)
    
    if taxable_income <= 0.0:
        return 0.0, 0.0
    
    withholding = 0.0
    last = 0.0
    for row in tax_table:
        amt, rate, flat_fee = row
        if taxable_income <= float(amt):
            withholding = (((taxable_income - last) * (rate / 100)) + flat_fee)
            break
        last = amt

    withholding = max(withholding, 0.0)
    withholding /= pay_periods
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
