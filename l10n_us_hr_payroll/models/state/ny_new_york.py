# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def ny_new_york_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'NY'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('ny_it2104_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    tax_table = payslip.rule_parameter('us_ny_sit_tax_rate')[filing_status].get(schedule_pay)
    allowances = payslip.contract_id.us_payroll_config_value('ny_it2104_sit_allowances')
    over_10_deduction = payslip.rule_parameter('us_ny_sit_over_10_exemption_rate')[schedule_pay]
    deduction_exemption = payslip.rule_parameter('us_ny_sit_deduction_exemption_rate')[filing_status].get(schedule_pay)

    if allowances > 10:
        if filing_status == 'single':
            wage -= over_10_deduction[0] + over_10_deduction[2] * allowances
        elif filing_status == 'married':
            wage -= over_10_deduction[1] + over_10_deduction[2] * allowances

    else:
        if filing_status == 'single':
            wage -= deduction_exemption[allowances]
        elif filing_status == 'married':
            wage -= deduction_exemption[allowances]
    last = 0.0
    withholding = 0.0
    for row in tax_table:
        amt, rate, flat_fee = row
        if wage <= float(amt):
            withholding = ((wage - last) * rate) + flat_fee
            break
        last = amt

    withholding = max(withholding, 0.0)
    withholding += additional
    return wage, -((withholding / wage) * 100.0)
