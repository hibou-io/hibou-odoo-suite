# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestPePayslip, process_payslip


class Test2020(TestPePayslip):

    ###
    #   2020 Taxes and Rates
    ###

    def test_2020_taxes(self):
        # High salary to hit the maximum for AFP_SEGURO
        salary = 8000.00

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        retirement_type='afp',
                                        afp_type='profuturo',
                                        afp_comision_type='mixta',
                                        comp_ss_type='essalud',
                                        )
        self._log(contract.read())

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], -cats['GROSS'] * (10.0 / 100.0))
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], -cats['GROSS'] * (1.35 / 100.0))
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION_MIXTA'], -cats['GROSS'] * (0.67 / 100.0))
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], -cats['GROSS'] * (6.75 / 100.0))

        process_payslip(payslip)
        
        self._log('2020 tax second payslip:')
        payslip = self._createPayslip(employee, '2020-02-01', '2020-02-28')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], -cats['GROSS'] * (10.0 / 100.0))
        
        self.assertTrue(cats['GROSS'] < 9707.03)
        # Seguro has a wage base.
        second_seguro = -(9707.03 - cats['GROSS']) * (1.35 / 100.0)
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], second_seguro)
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION_MIXTA'], -cats['GROSS'] * (0.67 / 100.0))
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], -cats['GROSS'] * (6.75 / 100.0))
        
        process_payslip(payslip)
        
        self._log('2020 tax third payslip:')
        payslip = self._createPayslip(employee, '2020-03-01', '2020-03-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], -cats['GROSS'] * (10.0 / 100.0))
        
        self.assertTrue(cats['GROSS'] < 9707.03)
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], 0.0)
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION_MIXTA'], -cats['GROSS'] * (0.67 / 100.0))
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], -cats['GROSS'] * (6.75 / 100.0))
        
        process_payslip(payslip)
    
    def test_2020_onp(self):
        salary = 3500.00

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        retirement_type='onp',
                                        onp_rule_id=self.env.ref('l10n_pe_hr_payroll.hr_payroll_rule_ee_onp').id,
                                        comp_ss_type='essalud',
                                        )
        self._log(contract.read())

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], 0.0)
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], 0.0)
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION_MIXTA'], 0.0)
        self.assertPayrollEqual(cats['EE_PE_ONP'], -cats['GROSS'] * (13.0 / 100.0))
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], -cats['GROSS'] * (6.75 / 100.0))

        process_payslip(payslip)
    
    def test_2020_ir_5ta_cat(self):
        salary = 1500.00

        employee = self._createEmployee()

        contract = self._createContract(employee,
                                        wage=salary,
                                        retirement_type='onp',
                                        onp_rule_id=self.env.ref('l10n_pe_hr_payroll.hr_payroll_rule_ee_onp').id,
                                        comp_ss_type='essalud',
                                        )

        self._log('2020 tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_IR_5TA_CAT'], 0.0)
        payslip.state = 'cancel'
        payslip.unlink()
        
        # larger salary to trigger calculation
        salary = 3000.0
        contract.wage = salary
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        self.assertPayrollEqual(cats['GROSS'], salary)
        self.assertPayrollEqual(rules['EE_PE_IR_5TA_CAT'], -74.67)
