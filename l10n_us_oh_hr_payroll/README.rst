*******************************
Hibou - US Payroll - Ohio State
*******************************

Calculations and contribution registers for Ohio State Payroll.

For more information and add-ons, visit `Hibou.io <https://hibou.io/>`_.

=============
Main Features
=============

* New Ohio Department of Revenue partner
* Contribution Registers for:
     * Ohio Department of Revenue - Unemployment
     * Ohio Department of Revenue - Income Tax withholding
* Contract level Ohio Withholding Allowance
* Company level Ohio Unemployment Rate

.. image:: https://user-images.githubusercontent.com/15882954/41481725-e1cbd3c4-7087-11e8-8bf7-84843bb2f943.png
    :alt: 'Employee Contract Detail'
    :width: 988
    :align: left

USA Ohio Employee added to Contract Salary Structure Menu

.. image:: https://user-images.githubusercontent.com/15882954/41481743-f1eceb4e-7087-11e8-8d09-dd45551a3fa4.png
    :alt: 'Computed Pay Slip Detail'
    :width: 988
    :align: left

New Payslip Categories for:

* Ohio Income Withholding
* Ohio Unemployment - Wages
* Ohio Unemployment

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
        'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_wages_2018',
        'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_unemp_2018',
        'l10n_us_oh_hr_payroll.hr_payroll_rules_oh_inc_withhold_2018',
    ]
    for rule_id in rules:
        migrate_rule_name(rule_id)

    env.cr.commit()


=======
License
=======
Please see `LICENSE <https://github.com/hibou-io/hibou-odoo-suite/blob/master/LICENSE>`_.
Copyright Hibou Corp. 2018
