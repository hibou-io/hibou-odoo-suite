*************************************
Hibou - US Payroll - California State
*************************************

Calculations and contribution registers for California State Payroll.

For more information and add-ons, visit `Hibou.io <https://hibou.io/>`_.

=============
Main Features
=============

* Contribution registers and partners for:
     * California Department of Taxation - Unemployment Insurance Tax
     * California Department of Taxation - Income Tax Withholding
     * California Department of Taxation - Employee Training Tax
     * California Department of Taxation - State Disability Insurance

* Contract level California Exemptions and California State Disability Insurance
* Company level California Unemployment Insurance Tax and California Employee Training Tax

.. image:: https://user-images.githubusercontent.com/15882954/41482877-d1311214-708b-11e8-9400-3bc5c134b836.png
    :alt: 'Employee Contract Detail'
    :width: 988
    :align: left

USA California Employee Added to  Contract Salary Structure Menu

.. image:: https://user-images.githubusercontent.com/15882954/41482910-ef25bbd0-708b-11e8-8720-d2065149f953.png
    :alt: 'Computed Pay Slip Detail'
    :width: 988
    :align: left

New Payslip Categories for:

* California Income Withholding
* California State Disability Insurance - Wages
* California State Disability Insurance
* California Employee Training Tax - Wages
* California Unemployment Insurance Tax - Wages
* California Unemployment Insurance Tax
* California Employee Training Tax

Upgrading to 11.0.2018.1.0
==========================

If you were using this prior to November 2018, then you have more Contribution registers
and partners than you need!  Simply run the following before installing the new code and upgrading.

Odoo Shell code::

    main_cr = env.ref('l10n_us_ca_hr_payroll.contrib_register_cador_uit')
    old_1 = env.ref('l10n_us_ca_hr_payroll.contrib_register_cador_withhold')
    old_2 = env.ref('l10n_us_ca_hr_payroll.contrib_register_cador_ett')
    old_3 = env.ref('l10n_us_ca_hr_payroll.contrib_register_cador_sdi')
    lines = env['hr.payslip.line'].search([('register_id', 'in', [old_1.id, old_2.id, old_3.id])])
    lines.write({'register_id': main_cr.id})
    env.cr.commit()


=======
License
=======
Please see `LICENSE <https://github.com/hibou-io/hibou-odoo-suite/blob/master/LICENSE>`_.
Copyright Hibou Corp. 2018
