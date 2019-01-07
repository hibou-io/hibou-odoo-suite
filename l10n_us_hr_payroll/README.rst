******************
Hibou - US Payroll
******************

Calculations and contribution registers for United States Payroll.

For more information and add-ons, visit `Hibou.io <https://hibou.io/>`_.

=============
Main Features
=============

* Contribution registers and partners for:
     * The Electronic Federal Tax Payment System (EFTPS) - Form 941
     * The Electronic Federal Tax Payment System (EFTPS) - Form 940
     * The Electronic Federal Tax Payment System (EFTPS) - Form 941 (FICA + Federal Withholding)
     * The Electronic Federal Tax Payment System (EFTPS) - Form 940 (FUTA)

* Contract level FICA Social Security
* Contract level FICA Employee Medicare
* Contract level FICA Employee Medicare Additional
* Contract level Federal Income Withholding
* Company level FICA Social Security
* Company level FICA Medicare
* Company level FUTA Federal Unemployment


.. image:: https://user-images.githubusercontent.com/15882954/41485460-76a0060c-7095-11e8-851a-fec562013ce4.png
    :alt: 'Employee Contract Detail'
    :width: 988
    :align: left

USA Employee added to  Contract Salary Structure Menu

.. image:: https://user-images.githubusercontent.com/15882954/41485484-880f0816-7095-11e8-9ad0-874b3270c308.png
    :alt: 'Computed Pay Slip Detail'
    :width: 988
    :align: left

Upgrading to 2019
==========================

If you were using this prior to January 2019, then you will need to run the following
migration script.

Odoo Shell code::

    def migrate_rule_name(rule_id):
        main = env.ref(rule_id)
        old_2017 = env.ref(rule_id.replace('2018', '2017'))
        old_2016 = env.ref(rule_id.replace('2018', '2016'))
        lines = env['hr.payslip.line'].search([('salary_rule_id', 'in', [old_2017.id, old_2016.id,])])
        lines.write({'salary_rule_id': main.id})

    rules = [
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_wages_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_wages_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_wages_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_ss_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fica_emp_m_add_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_single',
        'l10n_us_hr_payroll.hr_payroll_rules_fed_inc_withhold_2018_married',
        'l10n_us_hr_payroll.hr_payroll_rules_futa_wages_2018',
        'l10n_us_hr_payroll.hr_payroll_rules_futa_2018',
    ]
    for rule_id in rules:
        migrate_rule_name(rule_id)

    env.cr.commit()


=======
License
=======
Please see `LICENSE <https://github.com/hibou-io/hibou-odoo-suite/blob/master/LICENSE>`_.
Copyright Hibou Corp. 2018
