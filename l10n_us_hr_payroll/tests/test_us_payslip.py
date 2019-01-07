# -*- coding: utf-8 -*-

from logging import getLogger
from sys import float_info as sys_float_info

from openerp.tests import common
from openerp.tools.float_utils import float_round as odoo_float_round
from openerp.addons.l10n_us_hr_payroll.models.l10n_us_hr_payroll import USHrContract


def process_payslip(payslip):
    try:
        #v9
        payslip.process_sheet()
    except AttributeError:
        payslip.action_payslip_done()


class TestUsPayslip(common.TransactionCase):
    debug = False
    _logger = getLogger(__name__)

    float_info = sys_float_info

    def float_round(self, value, digits):
        return odoo_float_round(value, digits)

    _payroll_digits = -1

    @property
    def payroll_digits(self):
        if self._payroll_digits == -1:
            self._payroll_digits = self.env['decimal.precision'].precision_get('Payroll')
        return self._payroll_digits

    def _log(self, message):
        if self.debug:
            self._logger.warn(message)
            
    def _createEmployee(self):
        return self.env['hr.employee'].create({
            'birthday': '1985-03-14',
            'country_id': self.ref('base.us'),
            'department_id': self.ref('hr.dep_rd'),
            'gender': 'male',
            'name': 'Jared'
        })

    def _createContract(self, employee, salary,
                        schedule_pay='monthly',
                        w4_allowances=0,
                        w4_filing_status='single',
                        w4_is_nonresident_alien=False,
                        w4_additional_withholding=0.0,
                        external_wages=0.0,
                        struct_id=False,
                        futa_type=USHrContract.FUTA_TYPE_NORMAL,
                        ):
        if not struct_id:
            struct_id = self.ref('l10n_us_hr_payroll.hr_payroll_salary_structure_us_employee')

        return self.env['hr.contract'].create({
            'date_start': '2016-01-01',
            'date_end': '2030-12-31',
            'name': 'Contract for Jared 2016',
            'wage': salary,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': employee.id,
            'struct_id': struct_id,
            'working_hours': self.ref('resource.timesheet_group1'),
            'schedule_pay': schedule_pay,
            'w4_allowances': w4_allowances,
            'w4_filing_status': w4_filing_status,
            'w4_is_nonresident_alien': w4_is_nonresident_alien,
            'w4_additional_withholding': w4_additional_withholding,
            'external_wages': external_wages,
            'futa_type': futa_type,
            'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
        })

    def _createPayslip(self, employee, date_from, date_to):
        return self.env['hr.payslip'].create({
            'employee_id': employee.id,
            'date_from': date_from,
            'date_to': date_to
        })

    def _getCategories(self, payslip):
        detail_lines = payslip.details_by_salary_rule_category
        categories = {}
        for line in detail_lines:
            self._log(' line code: ' + str(line.code) +
                      ' category code: ' + line.category_id.code +
                      ' total: ' + str(line.total) +
                      ' rate: ' + str(line.rate) +
                      ' amount: ' + str(line.amount))
            if line.category_id.code not in categories:
                categories[line.category_id.code] = line.total
            else:
                categories[line.category_id.code] += line.total

        return categories

    def assertPayrollEqual(self, first, second):
        self.assertAlmostEqual(first, second, self.payroll_digits)

    def test_semi_monthly(self):
        salary = 80000.0
        employee = self._createEmployee()
        contract = self._createContract(employee, salary, schedule_pay='semi-monthly')
        payslip = self._createPayslip(employee, '2016-01-01', '2016-01-14')

        payslip.compute_sheet()
