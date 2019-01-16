**********************************
Hibou - US Payroll - Florida State
**********************************

Calculations and contribution registers for Florida State Payroll.

For more information and add-ons, visit `Hibou.io <https://hibou.io/>`_.

=============
Main Features
=============

* New Partner and Contribution Register for Florida Department of Revenue
* Company level Florida Unemployment Rate

.. image:: https://user-images.githubusercontent.com/15882954/41440232-a2ca8cb0-6fe2-11e8-9640-0bfd61ae6108.png
    :alt: 'Employee Contract Detail'
    :width: 988
    :align: left

USA Florida Employee Added to Contract Salary Structure Menu

.. image:: https://user-images.githubusercontent.com/15882954/41440247-b7b42744-6fe2-11e8-8ffb-d259eb893646.png
    :alt: 'Computed Pay Slip Detail'
    :width: 988
    :align: left

New Payslip Categories for:

* Florida Unemployment
* Florida Unemployment - Wages

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
        'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_wages_2018',
        'l10n_us_fl_hr_payroll.hr_payroll_rules_fl_unemp_2018',
    ]
    for rule_id in rules:
        migrate_rule_name(rule_id)

    env.cr.commit()



=======
License
=======
Please see `LICENSE <https://github.com/hibou-io/hibou-odoo-suite/blob/master/LICENSE>`_.
Copyright Hibou Corp. 2018
