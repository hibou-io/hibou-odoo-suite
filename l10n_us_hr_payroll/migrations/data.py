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
    'al_a4_filing_status': 'al_a4_sit_exemptions',
    'al_a4_dependents': 'al_a4_sit_dependents',
    'al_a4_personal_exemption': 'state_income_tax_exempt',
    'al_a4_additional_wh': 'state_income_tax_additional_withholding',
    
    'ar_w4_allowances': 'ar_ar4ec_sit_allowances',
    'ar_w4_tax_exempt': 'state_income_tax_exempt',
    'ar_w4_additional_wh': 'state_income_tax_additional_withholding',

    'az_a4_withholding_percentage': 'az_a4_sit_withholding_percentage',
    'az_a4_additional_withholding': 'state_income_tax_additional_withholding',

    'ca_de4_allowances': 'ca_de4_sit_allowances',
    'ca_additional_allowances': 'ca_de4_sit_additional_allowances',
    'ca_de4_filing_status': 'ca_de4_sit_filing_status',

    'ct_w4na_code': 'ct_w4na_sit_code',
    'ct_w4na_wh_amount': 'state_income_tax_additional_withholding',

    'ga_g4_filing_status': 'ga_g4_sit_filing_status',
    'ga_g4_dependent_allowances': 'ga_g4_sit_dependent_allowances',
    'ga_g4_additional_allowances': 'ga_g4_sit_additional_allowances',
    'ga_g4_additional_wh': 'state_income_tax_additional_withholding',

    'ms_89_350_filing_status': 'ms_89_350_sit_filing_status',
    'ms_89_350_exemption': 'ms_89_350_sit_exemption_value',
    'ms_89_350_additional_withholding': 'state_income_tax_additional_withholding',

    'mt_mw4_additional_withholding': 'state_income_tax_additional_withholding',
    'mt_mw4_exemptions': 'mt_mw4_sit_exemptions',
    'mt_mw4_exempt': 'mt_mw4_sit_exempt',

    'oh_additional_withholding': 'state_income_tax_additional_withholding',
    'oh_income_allowances': 'oh_it4_sit_exemptions',

    'pa_additional_withholding': 'state_income_tax_additional_withholding',

    'va_va4_exemptions': 'va_va4_sit_exemptions',

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

    'l10n_us_ga_hr_payroll.hr_payroll_ga_unemp_wages',
    'l10n_us_ga_hr_payroll.hr_payroll_ga_unemp',
    'l10n_us_ga_hr_payroll.hr_payroll_ga_income_withhold',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_unemp_wages',

    'l10n_us_ms_hr_payroll.hr_payroll_ms_unemp_wages',
    'l10n_us_ms_hr_payroll.hr_payroll_ms_unemp',
    'l10n_us_ms_hr_payroll.hr_payroll_ms_income_withhold',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_unemp_wages',

    'l10n_us_mt_hr_payroll.hr_payroll_mt_unemp_wages',
    'l10n_us_mt_hr_payroll.hr_payroll_mt_unemp',
    'l10n_us_mt_hr_payroll.hr_payroll_mt_income_withhold',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_unemp_wages',

    'l10n_us_oh_hr_payroll.hr_payroll_oh_unemp_wages',
    'l10n_us_oh_hr_payroll.hr_payroll_oh_unemp',
    'l10n_us_oh_hr_payroll.hr_payroll_oh_income_withhold',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_wages_2018',

    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_wages',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_employee',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_unemp_company',
    'l10n_us_pa_hr_payroll.hr_payroll_pa_withhold',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_wages_2018',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_add',

    'l10n_us_tx_hr_payroll.contrib_register_txdor',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_unemp_wages',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_unemp',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_oa',
    'l10n_us_tx_hr_payroll.hr_payroll_tx_etia',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_unemp_wages_2018',

    'l10n_us_va_hr_payroll.hr_payroll_va_unemp_wages',
    'l10n_us_va_hr_payroll.hr_payroll_va_unemp',
    'l10n_us_va_hr_payroll.hr_payroll_va_income_withhold',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_unemp_wages_2018',

    'l10n_us_wa_hr_payroll.hr_payroll_wa_unemp_wages',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_unemp',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_wa_lni_withhold',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_unemp_wages_2018',

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

    'l10n_us_ga_hr_payroll.res_partner_ga_dol_unemp': 'l10n_us_hr_payroll.res_partner_us_ga_dor',
    'l10n_us_ga_hr_payroll.res_partner_ga_dor_withhold': 'l10n_us_hr_payroll.res_partner_us_ga_dor_sit',
    'l10n_us_ga_hr_payroll.contrib_register_ga_dol_unemp': 'l10n_us_hr_payroll.contrib_register_us_ga_dor',
    'l10n_us_ga_hr_payroll.contrib_register_ga_dor_withhold': 'l10n_us_hr_payroll.contrib_register_us_ga_dor_sit',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ga_suta',
    'l10n_us_ga_hr_payroll.hr_payroll_rules_ga_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ga_sit',

    'l10n_us_ms_hr_payroll.res_partner_msdor_unemp': 'l10n_us_hr_payroll.res_partner_us_ms_dor',
    'l10n_us_ms_hr_payroll.res_partner_msdor_withhold': 'l10n_us_hr_payroll.res_partner_us_ms_dor_sit',
    'l10n_us_ms_hr_payroll.contrib_register_msdor_unemp': 'l10n_us_hr_payroll.contrib_register_us_ms_dor',
    'l10n_us_ms_hr_payroll.contrib_register_msdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_ms_dor_sit',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_ms_suta',
    'l10n_us_ms_hr_payroll.hr_payroll_rules_ms_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_ms_sit',

    'l10n_us_mt_hr_payroll.res_partner_mtdor_unemp': 'l10n_us_hr_payroll.res_partner_us_mt_dor',
    'l10n_us_mt_hr_payroll.res_partner_mtdor_withhold': 'l10n_us_hr_payroll.res_partner_us_mt_dor_sit',
    'l10n_us_mt_hr_payroll.contrib_register_mtdor_unemp': 'l10n_us_hr_payroll.contrib_register_us_mt_dor',
    'l10n_us_mt_hr_payroll.contrib_register_mtdor_withhold': 'l10n_us_hr_payroll.contrib_register_us_mt_dor_sit',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_unemp': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta',
    'l10n_us_mt_hr_payroll.hr_payroll_rules_mt_inc_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_mt_sit',

    'l10n_us_oh_hr_payroll.res_partner_ohdor_unemp': 'l10n_us_hr_payroll.res_partner_us_oh_dor',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_withhold': 'l10n_us_hr_payroll.res_partner_us_oh_dor_sit',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_unemp': 'l10n_us_hr_payroll.res_partner_us_oh_dor',
    'l10n_us_oh_hr_payroll.res_partner_ohdor_withhold': 'l10n_us_hr_payroll.res_partner_us_oh_dor_sit',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_oh_suta',
    'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_oh_sit',

    'l10n_us_pa_hr_payroll.res_partner_pador_unemp_company': 'l10n_us_hr_payroll.res_partner_us_pa_dor',
    'l10n_us_pa_hr_payroll.res_partner_pador_withhold': 'l10n_us_hr_payroll.res_partner_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.contrib_register_pador_unemp_company': 'l10n_us_hr_payroll.contrib_register_us_pa_dor',
    'l10n_us_pa_hr_payroll.contrib_register_pador_withhold': 'l10n_us_hr_payroll.contrib_register_us_pa_dor_sit',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_employee_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_unemp_company_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_pa_suta',
    'l10n_us_pa_hr_payroll.hr_payroll_rules_pa_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_pa_sit',

    'l10n_us_tx_hr_payroll.res_partner_txdor': 'l10n_us_hr_payroll.res_partner_us_tx_dor',
    'l10n_us_tx_hr_payroll.contrib_register_txdor': 'l10n_us_hr_payroll.contrib_register_us_tx_dor',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_oa_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta_oa',
    'l10n_us_tx_hr_payroll.hr_payroll_rules_tx_etia_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_tx_suta_etia',

    'l10n_us_va_hr_payroll.res_partner_vador_unemp': 'l10n_us_hr_payroll.res_partner_us_va_dor',
    'l10n_us_va_hr_payroll.res_partner_vador_withhold': 'l10n_us_hr_payroll.res_partner_us_va_dor_sit',
    'l10n_us_va_hr_payroll.contrib_register_vador_unemp': 'l10n_us_hr_payroll.contrib_register_us_va_dor',
    'l10n_us_va_hr_payroll.contrib_register_vador_withhold': 'l10n_us_hr_payroll.contrib_register_us_va_dor_sit',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_va_suta',
    'l10n_us_va_hr_payroll.hr_payroll_rules_va_inc_withhold_2018': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_va_sit',

    'l10n_us_wa_hr_payroll.res_partner_wador_unemp': 'l10n_us_hr_payroll.res_partner_us_wa_dor',
    'l10n_us_wa_hr_payroll.res_partner_wador_lni': 'l10n_us_hr_payroll.res_partner_us_wa_dor_lni',
    'l10n_us_wa_hr_payroll.contrib_register_wador_unemp': 'l10n_us_hr_payroll.contrib_register_us_wa_dor',
    'l10n_us_wa_hr_payroll.contrib_register_wador_lni': 'l10n_us_hr_payroll.contrib_register_us_wa_dor_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_unemp_2018': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_suta',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_lni_withhold': 'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_lni',
    'l10n_us_wa_hr_payroll.hr_payroll_rules_wa_lni': 'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_lni',

}

XMLIDS_COPY_ACCOUNTING_2020 = {
    'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta': [
        'l10n_us_hr_payroll.hr_payroll_rule_er_us_mt_suta_aft',
    ],
    'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_lni': [
        'l10n_us_hr_payroll.hr_payroll_rule_er_us_wa_fml',
    ],
    'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_lni': [
        'l10n_us_hr_payroll.hr_payroll_rule_ee_us_wa_fml',
    ],
}
