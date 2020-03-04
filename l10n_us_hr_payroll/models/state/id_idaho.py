# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .general import _state_applies, sit_wage


def id_idaho_state_income_withholding(payslip, categories, worked_days, inputs):
    """
    Returns SIT eligible wage and rate.

    :return: result, result_rate (wage, percent)
    """
    state_code = 'ID'
    if not _state_applies(payslip, state_code):
        return 0.0, 0.0

    # Determine Wage
    wage = sit_wage(payslip, categories)
    if not wage:
        return 0.0, 0.0

    filing_status = payslip.contract_id.us_payroll_config_value('id_w4_sit_filing_status')
    if not filing_status:
        return 0.0, 0.0

    schedule_pay = payslip.contract_id.schedule_pay
    allowances = payslip.contract_id.us_payroll_config_value('id_w4_sit_allowances')
    ictcat_table = payslip.rule_parameter('us_id_sit_ictcat_rate')[schedule_pay]
    tax_table = payslip.rule_parameter('us_id_sit_tax_rate')[filing_status].get(schedule_pay)

    taxable_income = wage - (ictcat_table * allowances)
    withholding = 0.0
    last = 0.0
    for row in tax_table:
        if taxable_income <= float(row[0]):
            withholding = row[1] + ((row[2] / 100.0) * (taxable_income - last))
            break
        last = row[0]

    withholding = max(withholding, 0.0)
    withholding = round(withholding)
    return wage, -((withholding / wage) * 100.0)
