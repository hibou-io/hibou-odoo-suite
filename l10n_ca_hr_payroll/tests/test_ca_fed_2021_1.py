# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields
from .common import TestCAPayslip
import logging

_logger = logging.getLogger("__name__")


class TestPayslip(TestCAPayslip):

    def test_basic_federal_tax_monthly(self):
        salary = 7000.0
        date_from = '2021-01-01'
        date_to = '2021-01-31'

        employee = self._createEmployee()

        # not this would make
        # Monthly
        # Alberta
        # Federal Claim 13808
        # Provincial Claim 19369
        contract = self._createContract(employee,
                                        wage=salary,
                                        is_cpp_exempt=True,
                                        is_ei_exempt=True,
                                        )

        self._log('2021 tax first payslip:')

        payslip = self._createPayslip(employee, date_from, date_to)
        self.assertEqual(payslip.contract_id, contract)
        self.assertEqual(payslip.struct_id, self.structure)
        self.assertEqual(payslip.date_from, fields.Date.from_string(date_from))
        self.assertEqual(payslip.date_to, fields.Date.from_string(date_to))

        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 7000.0)
        self.assertEqual(cats.get('EE_CA_CPP', 0.0), 0.0)
        self.assertEqual(cats.get('EE_CA_EI', 0.0), 0.0)
        self.assertPayrollAlmostEqual(cats['EE_CA_FIT'], -1022.02)  # amount from apps.cra-arc.gc.ca

    def test_basic_federal_tax_monthly_2(self):
        salary = 2000.0
        date_from = '2021-01-01'
        date_to = '2021-01-31'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        is_cpp_exempt=True,
                                        is_ei_exempt=True,
                                        )
        payslip = self._createPayslip(employee, date_from, date_to)
        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 2000.0)
        self.assertEqual(cats.get('EE_CA_CPP', 0.0), 0.0)
        self.assertEqual(cats.get('EE_CA_EI', 0.0), 0.0)
        self.assertPayrollAlmostEqual(cats['EE_CA_FIT'], -111.69)

    def test_basic_federal_tax_weekly(self):
        salary = 2000.0
        date_from = '2021-01-25'
        date_to = '2021-01-31'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        is_cpp_exempt=True,
                                        is_ei_exempt=True,
                                        schedule_pay='weekly'
                                        )
        payslip = self._createPayslip(employee, date_from, date_to)
        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 2000.0)
        self.assertEqual(cats.get('EE_CA_CPP', 0.0), 0.0)
        self.assertEqual(cats.get('EE_CA_EI', 0.0), 0.0)
        self.assertPayrollAlmostEqual(cats['EE_CA_FIT'], -321.05)  # note calculator says 321.00

    def test_low_wage_additional(self):
        salary = 1000.0
        date_from = '2021-01-01'
        date_to = '2021-01-31'
        test_additional = 100.0

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        is_cpp_exempt=True,
                                        is_ei_exempt=True,
                                        fed_td1_additional=test_additional,
                                        )

        payslip = self._createPayslip(employee, date_from, date_to)
        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 1000.0)
        self.assertEqual(cats.get('EE_CA_CPP', 0.0), 0.0)
        self.assertEqual(cats.get('EE_CA_EI', 0.0), 0.0)
        self.assertEqual(cats['EE_CA_FIT'], -test_additional)

    def test_basic_ei(self):
        salary = 7000.0
        date_from = '2021-01-01'
        date_to = '2021-01-31'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        is_cpp_exempt=True,
                                        is_ei_exempt=False
                                        )

        payslip = self._createPayslip(employee, date_from, date_to)
        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 7000.0)
        self.assertEqual(cats.get('EE_CA_CPP', 0.0), 0.0)
        self.assertAlmostEqual(cats['EE_CA_EI'], -110.60)
        self.assertPayrollAlmostEqual(cats['EE_CA_FIT'], -1010.90)
