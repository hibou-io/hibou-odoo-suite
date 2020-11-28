from .common import TestPayslip, process_payslip


class TestContractWageType(TestPayslip):

    def test_per_contract_wage_type_salary(self):
        self.debug = True
        salary = 80000.0
        employee = self._createEmployee()
        contract = self._createContract(employee, wage=salary, hourly_wage=salary/100.0, wage_type='monthly', schedule_pay='bi-weekly')
        payslip = self._createPayslip(employee, '2019-12-30', '2020-01-12')
        self.assertEqual(contract.wage_type, 'monthly')
        self.assertEqual(payslip.wage_type, 'monthly')
        cats = self._getCategories(payslip)
        self.assertEqual(cats['BASIC'], salary)

    def test_per_contract_wage_type_hourly(self):
        self.debug = True
        hourly_wage = 21.50
        employee = self._createEmployee()
        contract = self._createContract(employee, wage=hourly_wage*100.0, hourly_wage=hourly_wage, wage_type='hourly', schedule_pay='bi-weekly')
        payslip = self._createPayslip(employee, '2019-12-30', '2020-01-12')
        self.assertEqual(contract.wage_type, 'hourly')
        self.assertEqual(payslip.wage_type, 'hourly')
        cats = self._getCategories(payslip)
        self.assertEqual(cats['BASIC'], hourly_wage * 80.0)
