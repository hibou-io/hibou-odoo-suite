# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

FIELDS_CONTRACT_TO_US_PAYROLL_FORMS_2020 = {
    # Federal
    'w4_allowances': 'fed_941_fit_w4_allowances',
    'w4_filing_status': 'fed_941_fit_w4_filing_status',
    'w4_is_nonresident_alien': 'fed_941_fit_w4_is_nonresident_alien',
    'w4_additional_withholding': 'fed_941_fit_w4_additional_withholding',
    'fica_exempt': 'fed_941_fica_exempt',
    'futa_type': 'fed_940_type',
    # State
    'pa_additional_withholding': 'state_income_tax_additional_withholding',
}

XMLIDS_TO_REMOVE_2020 = [
    # Federal
    # Categories -- These are now all up in the EE FICA or ER FICA
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_add',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_add_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_comp_m',
    'l10n_us_hr_payroll.hr_payroll_futa_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_m_wages',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_ss_wages',
    # Rules -- These are mainly Wage rules or were simplified to a single rule
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_futa_wages_2018',
    'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_married',
    # State
    'l10n_us_fl_hr_payroll.hr_payroll_fl_unemp_wages',
    'l10n_us_fl_hr_payroll.hr_payroll_fl_unemp',
    'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_wages_2018',
    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_wages',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_company',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_withhold',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_wages_2018',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_add',
]

XMLIDS_TO_RENAME_2020 = {
    # Federal
    'l10n_us_hr_payroll.hr_payroll_futa': 'l10n_us_hr_payroll.hr_payroll_category_er_fed_940',
    'l10n_us_hr_payroll.hr_payroll_fica_emp_ss': 'l10n_us_hr_payroll.hr_payroll_category_ee_fed_941',
    'l10n_us_hr_payroll.hr_payroll_fed_income_withhold': 'l10n_us_hr_payroll.hr_payroll_category_ee_fed_941_fit',
    'l10n_us_hr_payroll.hr_payroll_fica_comp_ss': 'l10n_us_hr_payroll.hr_payroll_category_er_fed_941',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_ss',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_m',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_m_add',
    'l10n_us_hr_payroll.hr_payroll_rules_futa_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_940',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_comp_ss': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_941_ss',
    'l10n_us_hr_payroll.hr_payroll_rules_fica_comp_m': 'l10n_us_hr_payroll.hr_payroll_rule_er_fed_941_m',
    'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_single': 'l10n_us_hr_payroll.hr_payroll_rule_ee_fed_941_fit',
    # State
    'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_fl_suta',
    'l10n_us_fl_hr_payroll.res_partner_fldor': 'l10n_us_hr_payroll.res_partner_us_fl_dor',
    'l10n_us_fl_hr_payroll.contrib_register_fldor': 'l10n_us_hr_payroll.contrib_register_us_fl_dor',
    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_company': 'l10n_us_hr_payroll.res_partner_us_pa_dor',
    'l10n_us_pa_hr_payroll.res_partner_pador_withhold': 'l10n_us_hr_payroll.res_partner_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_company': 'l10n_us_hr_payroll.contrib_register_us_pa_dor',
    'l10n_us_pa_hr_payroll.contrib_register_pador_withhold': 'l10n_us_hr_payroll.contrib_register_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_employee_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_company_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_sit',
}
