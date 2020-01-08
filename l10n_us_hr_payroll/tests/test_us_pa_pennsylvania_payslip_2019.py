# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestUsPayslip, process_payslip


class TestUsPAPayslip(TestUsPayslip):
    ###
    #    Taxes and Rates
    ###
    PA_UNEMP_MAX_WAGE = 10000.0
    ER_PA_UNEMP = -3.6890 / 100.0
    EE_PA_UNEMP = -0.06 / 100.0
    PA_INC_WITHHOLD = 3.07

    def test_2019_taxes(self):
        salary = 4166.67
        wh = -127.92


        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_us_state('PA'))

        self._log('2019 Pennsylvania tax first payslip:')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-31')
        payslip.compute_sheet()

        cats = self._getCategories(payslip)

        self.assertPayrollEqual(cats['EE_US_SUTA'], cats['GROSS'] * self.EE_PA_UNEMP)
        self.assertPayrollEqual(cats['ER_US_SUTA'], cats['GROSS'] * self.ER_PA_UNEMP)
        self.assertPayrollEqual(cats['EE_US_SIT'], wh)
