# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


def _compute_annual_taxable_income(payslip, categories):
    """
    A = Annual taxable income
    = [P × (I – F – F2 – U1 )] – HD – F1
    """
    P = payslip.dict.get_pay_periods_in_year()
    I = categories.GROSS \
        - categories.ALW_FIT_EXEMPT \
        + categories.DED_FIT_EXEMPT
    F = 0.0  # Payroll deductions for RPP or RRSP ...
    F2 = 0.0
    U1 = 0.0  # Union Dues
    HD = 0.0  # Annual deduction for living in a prescribed zone Form TD1
    F1 = 0.0  # Annual deductions such as child care and authorized
    A = (P * (I - F - F2 - U1)) - HD - F1
    return A


def ca_fit_federal_income_tax_withholding(payslip, categories, worked_days, inputs):
    L = payslip.contract_id.ca_payroll_config_value('fed_td1_additional')
    A = _compute_annual_taxable_income(payslip, categories)
    # If the result is negative, T = L.
    if A <= 0.0 and L:
        return -L, 1.0
    elif A <= 0.0:
        return 0.0, 0.0

    TC = payslip.contract_id.ca_payroll_config_value('fed_td1_total_claim_amount')
    P = payslip.dict.get_pay_periods_in_year()

    """
    T3 = Annual basic federal tax
    = (R × A) – K – K1 – K2 – K3 – K4
    If the result is negative, T3 = $0.
    """
    rates = payslip.rule_parameter('ca_fed_tax_rate')
    for annual_taxable_income, rate, federal_constant in rates:
        annual_taxable_income = float(annual_taxable_income)
        if A < annual_taxable_income:
            break
        R, K = rate, federal_constant

    K1 = 0.15 * TC

    K2 = 0.0
    if not payslip.contract_id.ca_payroll_config_value('is_cpp_exempt'):
        C = categories.EE_CA_CPP
        K2 += 0.15 * min(P * C, 3166.45)  # min because we can only have up to
    if not payslip.contract_id.ca_payroll_config_value('is_ei_exempt'):
        EI = categories.EE_CA_EI
        K2 += 0.15 * min(P * EI, 889.54)
    K3 = 0.0  # medical
    CEA = 1257.0  # TODO this is an indexed parameter
    K4 = min(0.15 * A, 0.15 * CEA)

    T3 = (R * A) - K - K1 - K2 - K3 - K4

    LCF = min(750.0, 0.15 * 0.0)  # 0.0 => amount deducted or withheld during the year for the acquisition by the employee of approved shares of the capital stock of a prescribed labour-sponsored venture capital corporation
    T1 = T3 - LCF
    T = (T1 / P) + L
    if T > 0.0:
        return A, -(T / A * 100.0)
    return 0.0, 0.0
