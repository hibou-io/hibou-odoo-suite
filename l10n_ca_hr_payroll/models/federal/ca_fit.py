# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from ..state.general import _state_applies


def _compute_annual_taxable_income(payslip, categories):
    """
    A = Annual taxable income
    = [P × (I – F – F2 – U1 )] – HD – F1
    """
    P = payslip.dict.get_pay_periods_in_year()
    I = categories.GROSS \
        - categories.ALW_FIT_EXEMPT
    # F = 0.0  # Payroll deductions for RPP or RRSP ...
    # F2 = 0.0  # Annual Alimony or maintenance payments
    # U1 = 0.0  # Union Dues
    I += categories.DED_FIT_EXEMPT
    
    HD = 0.0  # Annual deduction for living in a prescribed zone Form TD1
    F1 = 0.0  # Annual deductions such as child care and authorized
    # A = (P * (I - F - F2 - U1)) - HD - F1
    A = (P * I) - HD - F1
    return A

def ca_fit_k1_personal_tax_credit(payslip, categories, worked_days, inputs):
    TC = payslip.contract_id.ca_payroll_config_value('fed_td1_total_claim_amount')
    k1 = payslip.rule_parameter('ca_fed_k1')
    return k1 * TC

def ca_fit_k2_cpp_ei_tax_credit(payslip, categories, worked_days, inputs):
    P = payslip.dict.get_pay_periods_in_year()
    C = -categories.EE_CA_CPP
    EI = -categories.EE_CA_EI
    k2 = payslip.rule_parameter('ca_fed_k2')
    result = 0.0
    if _state_applies(payslip, 'QC'):
        pc_max = payslip.rule_parameter('ca_fed_k2q_pc_max')
        pei_max = payslip.rule_parameter('ca_fed_k2q_pei_max')
        pie = payslip.rule_parameter('ca_fed_k2q_pie')
        pie_max = payslip.rule_parameter('ca_fed_k2q_pie_max')
        IE = 0.0  # TODO get IE
        result = k2 * min(P * IE * pie, pie_max)
    else:
        pc_max = payslip.rule_parameter('ca_fed_k2_pc_max')
        pei_max = payslip.rule_parameter('ca_fed_k2_pei_max')
    
    if not payslip.contract_id.ca_payroll_config_value('is_cpp_exempt'):
        result += k2 * min(P * C, pc_max)
    
    if not payslip.contract_id.ca_payroll_config_value('is_ei_exempt'):
        result += k2 * min(P * EI, pei_max)
    
    return  result

def ca_fit_k3_other_tax_credits(payslip, categories, worked_days, inputs):
    # this could be a category (if it were a dummy category)
    # this could be a contract field, but what would it truely mean?
    # How would we know if we implemented this after the first pay period?
    # adjust (P * K3) / PR
    return 0.0

def ca_fit_k4_non_refunable_tax_credit(payslip, categories, worked_days, inputs):
    k4 = payslip.rule_parameter('ca_fed_k4')
    A = _compute_annual_taxable_income(payslip, categories)
    cea = payslip.rule_parameter('ca_fed_cea')
    return min(k4 * A, k4 * cea)

def ca_fit_t3_annual_basic_federal_tax(payslip, categories, worked_days, inputs):    
    """
    T3 = Annual basic federal tax
    = (R × A) – K – K1 – K2 – K3 – K4
    If the result is negative, T3 = $0.
    """
    A = _compute_annual_taxable_income(payslip, categories)
    rates = payslip.rule_parameter('ca_fed_tax_rate')
    for annual_taxable_income, rate, federal_constant in rates:
        annual_taxable_income = float(annual_taxable_income)
        if A < annual_taxable_income:
            break
        R, K = rate, federal_constant
    
    T3 = (R * A) - K
    T3 -= ca_fit_k1_personal_tax_credit(payslip, categories, worked_days, inputs)
    T3 -= ca_fit_k2_cpp_ei_tax_credit(payslip, categories, worked_days, inputs)
    T3 -= ca_fit_k3_other_tax_credits(payslip, categories, worked_days, inputs)
    T3 -= ca_fit_k4_non_refunable_tax_credit(payslip, categories, worked_days, inputs)
    if T3 < 0.0:
        return 0.0
    return T3

def ca_fit_t1_federal_income_tax_payable(payslip, categories, worked_days, inputs):
    T3 = ca_fit_t3_annual_basic_federal_tax(payslip, categories, worked_days, inputs)
    # Short out as it can only go down..
    if T3 <= 0.0:
        return 0.0
    
    amount_deducted_stock = 0.0
    # amount deducted or withheld during the year for the acquisition by the employee of approved shares of the capital stock of a prescribed labour-sponsored venture capital corporation
    # this amount could be a category, but it would need to be year to date.
    LCF = min(750.0, 0.15 * amount_deducted_stock)  # 0.0 => amount deducted or withheld during the year for the acquisition by the employee of approved shares of the capital stock of a prescribed labour-sponsored venture capital corporation
    
    if _state_applies(payslip, 'QC'):
        t1q = payslip.rule_parameter('ca_fed_t1q')
        T1 = (T3 - LCF) - (t1q * T3)
    elif payslip.contract_id.ca_payroll_config_value('is_outside_ca'):
        t1_outside = payslip.rule_parameter('ca_fed_t1_outside')
        T1 = T3 + (t1_outside * T3) - LCF
    else:
        T1 = T3 - LCF
    
    if T1 < 0.0:
        return 0.0
    return T1

def ca_fit_federal_income_tax_withholding(payslip, categories, worked_days, inputs):
    L = payslip.contract_id.ca_payroll_config_value('fed_td1_additional')
    A = _compute_annual_taxable_income(payslip, categories)
    # If the result is negative, T = L.
    if A <= 0.0 and L:
        return -L, 100.0
    elif A <= 0.0:
        return 0.0, 0.0
    
    T1 = ca_fit_t1_federal_income_tax_payable(payslip, categories, worked_days, inputs)
    if T1 <= 0.0 and L:
        return -L, 100.0
    elif T1 <= 0.0:
        return 0.0, 0.0
    
    P = payslip.dict.get_pay_periods_in_year()
    T = (T1 / P) + L
    if T > 0.0:
        T = round(T, 2)
        return A, -(T / A * 100.0)
    return 0.0, 0.0
