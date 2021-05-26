# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


def ca_ei(payslip, categories, worked_days, inputs):
    if payslip.contract_id.ca_payroll_config_value('is_ei_exempt'):
        return 0.0, 0.0
    IE = categories.GROSS  # TODO how to adjust
    year = payslip.dict.get_year()
    D1 = -payslip.sum_category('EE_CA_EI', str(year) + '-01-01', str(year + 1) + '-01-01')
    EI = round(min(889.54 - D1, 0.0158 * IE), 2)
    return -EI, 100.0
