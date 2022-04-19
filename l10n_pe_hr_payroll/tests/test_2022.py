# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestPePayslip, process_payslip


class Test2022(TestPePayslip):
    
    # AFP Constants
    AFP_PENSIONES = 0.1  # 10%
    AFP_SEGURO = 0.0174  # 1.74%
    AFP_COMISION = 0.0018  # 0.18%
    
    # ER ESSALUD
    ER_ESSALUD = 0.0675  # 6.75%

    ###
    #   2022 Taxes and Rates
    ###

    def test_2022_taxes(self):
        salary = 3290.0

        employee = self._createEmployee()

        contract = self._createContract(employee, wage=salary)
        self._log(contract.read())

        self._log('2022 tax first payslip:')
        payslip = self._createPayslip(employee, '2022-01-01', '2022-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)
        rules = self._getRules(payslip)
        # Employee
        self.assertPayrollEqual(cats['BASIC'], salary)
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], -cats['BASIC'] * self.AFP_PENSIONES)
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], -cats['BASIC'] * self.AFP_SEGURO)
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION'], -cats['BASIC'] * self.AFP_COMISION)
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], -cats['BASIC'] * self.ER_ESSALUD)

        process_payslip(payslip)
