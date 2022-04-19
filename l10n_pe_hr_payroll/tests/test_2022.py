# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestPePayslip, process_payslip


class Test2022(TestPePayslip):
    
    # AFP Constants
    AFP_PENSIONES = 0.1  # 10%
    AFP_SEGURO = 0.0174  # 1.74%
    AFP_COMISION = 0.0018  # 0.18%
    
    # ER ESSALUD
    ER_ESSALUD = 0.0675  # 6.75%
    
    # # FUTA Constants
    # FUTA_RATE_NORMAL = 0.6
    # FUTA_RATE_BASIC = 6.0
    # FUTA_RATE_EXEMPT = 0.0

    # # Wage caps
    # FICA_SS_MAX_WAGE = 147000.0
    # FICA_M_MAX_WAGE = float_info.max
    # FICA_M_ADD_START_WAGE = 200000.0
    # FUTA_MAX_WAGE = 7000.0

    # # Rates
    # FICA_SS = 6.2 / -100.0
    # FICA_M = 1.45 / -100.0
    # FUTA = FUTA_RATE_NORMAL / -100.0
    # FICA_M_ADD = 0.9 / -100.0

    ###
    #   2022 Taxes and Rates
    ###

    def test_2022_taxes(self):
        self.debug = True
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
        self.assertPayrollEqual(rules['EE_PE_AFP_PENSIONES'], cats['BASIC'] * self.AFP_PENSIONES)
        self.assertPayrollEqual(rules['EE_PE_AFP_SEGURO'], cats['BASIC'] * self.AFP_SEGURO)
        self.assertPayrollEqual(rules['EE_PE_AFP_COMISION'], cats['BASIC'] * self.AFP_COMISION)
        # Employer
        self.assertPayrollEqual(rules['ER_PE_ESSALUD'], cats['BASIC'] * self.ER_ESSALUD)

        process_payslip(payslip)
