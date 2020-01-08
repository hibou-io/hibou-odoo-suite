# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date
from .common import TestUsPayslip


class TestUsPAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    PA_UNEMP_MAX_WAGE = 10000.0
    ER_PA_UNEMP = 3.6890
    EE_PA_UNEMP = 0.06
    PA_INC_WITHHOLD = 3.07

    def test_2020_taxes(self):
        self._test_er_suta('PA', self.ER_PA_UNEMP, date(2020, 1, 1), wage_base=self.PA_UNEMP_MAX_WAGE)
        self._test_ee_suta('PA', self.EE_PA_UNEMP, date(2020, 1, 1))

        salary = 4166.67
        wh = -127.92
        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('PA'))

        self._log('2019 Pennsylvania tax first payslip:')
        payslip = self._createPayslip(employee, '2020-01-01', '2020-01-31')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)

        # Test Additional
        contract.us_payroll_config_id.state_income_tax_additional_withholding = 100.0
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh - 100.0)

        # Test Exempt
        contract.us_payroll_config_id.state_income_tax_exempt = True
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertPayrollEqual(cats.get('EE_US_SIT', 0.0), 0.0)
