# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def mo_missouri_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.
    WAGE = GROSS + DED_FIT_EXEMPT

    :return: result, result_rate (wage, percent)
    """
    state_code = 'MO'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('mo_mow4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    reduced_withholding = payslip.contract_id.us_payroll_config_value('mo_mow4_sit_withholding')
    if reduced_withholding:
        return wage, -((reduced_withholding / wage) * 100.0)

    pay_periods = payslip.dict.get_pay_periods_in_year()
    additional = payslip.contract_id.us_payroll_config_value('state_income_tax_additional_withholding')
    sit_table = payslip.rule_parameter('us_mo_sit_rate')
    deduction = payslip.rule_parameter('us_mo_sit_deduction')[filing_status]

    gross_taxable_income = wage * pay_periods
    gross_taxable_income -= deduction

    remaining_taxable_income = gross_taxable_income
    withholding = 0.0
    for amt, rate in sit_table:
        amt = float(amt)
        rate = rate / 100.0
        if (remaining_taxable_income - amt) > 0.0 or (remaining_taxable_income - amt) == 0.0:
            withholding += rate * amt
        else:
            withholding += rate * remaining_taxable_income
            break
        remaining_taxable_income = remaining_taxable_income - amt

    withholding /= pay_periods
    withholding += additional
    withholding = round(withholding)
    return wage, -((withholding / wage) * 100.0)
