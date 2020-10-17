from .common import TestUsPayslip, process_payslip


class TestSpecial(TestUsPayslip):
    def test_semi_monthly(self):
        salary = 80000.0
        employee = self._createEmployee()
        # so the schedule_pay is now on the Structure...
        contract = self._createContract(employee, wage=salary, schedule_pay='semi-monthly')
        payslip = self._createPayslip(employee, '2019-01-01', '2019-01-14')
        payslip.compute_sheet()

    def test_payslip_sum_behavior(self):
        us_structure = self.env.ref('l10n_us_hr_payroll.hr_payroll_structure')
        rule_category_comp = self.env.ref('hr_payroll.COMP')
        test_rule_category = self.env['hr.salary.rule.category'].create({
            'name': 'Test Sum Behavior',
            'code': 'test_sum_behavior',
            'parent_id': rule_category_comp.id,
        })
        test_rule = self.env['hr.salary.rule'].create({
            'sequence': 450,
            'struct_id': us_structure.id,
            'category_id': test_rule_category.id,
            'name': 'Test Sum Behavior',
            'code': 'test_sum_behavior',
            'condition_select': 'python',
            'condition_python': 'result = 1',
            'amount_select': 'code',
            'amount_python_compute': '''
ytd_category = payslip.sum_category('test_sum_behavior', '2020-01-01', '2021-01-01')
ytd_rule = payslip.sum('test_sum_behavior', '2020-01-01', '2021-01-01')
result = 0.0
if ytd_category != ytd_rule:
  # error
  result = -1.0
elif ytd_rule == 0.0:
  # first payslip in period
  result = 1.0
'''
        })
        salary = 80000.0
        employee = self._createEmployee()
        contract = self._createContract(employee, wage=salary, schedule_pay='bi-weekly')
        payslip = self._createPayslip(employee, '2019-12-30', '2020-01-12')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['test_sum_behavior'], 1.0)
        process_payslip(payslip)

        # Basic date_from behavior.
        self.env['ir.config_parameter'].set_param('hr_payroll.payslip.sum_behavior', 'date_from')
        # The the date_from on the last payslip will not be found
        payslip = self._createPayslip(employee, '2020-01-13', '2020-01-27')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['test_sum_behavior'], 1.0)

        # date_to behavior.
        self.env['ir.config_parameter'].set_param('hr_payroll.payslip.sum_behavior', 'date_to')
        # The date_to on the last payslip is found
        payslip = self._createPayslip(employee, '2020-01-13', '2020-01-27')
        payslip.compute_sheet()
        cats = self._getCategories(payslip)
        self.assertEqual(cats['test_sum_behavior'], 0.0)
