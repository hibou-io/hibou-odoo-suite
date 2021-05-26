# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from .common import TestCAPayslip
import logging

_logger = logging.getLogger("__name__")


class TestPayslip(TestCAPayslip):

    def test_tax_alberta(self):
        salary = 7000.0
        date_from = '2021-01-01'
        date_to = '2021-01-31'

        employee = self._createEmployee()
        contract = self._createContract(employee,
                                        wage=salary,
                                        state_id=self.get_ca_state('AB'))

        payslip = self._createPayslip(employee, date_from, date_to)
        # self.assertEqual(payslip.struct_type_id, )
        self.assertEqual(payslip.contract_id, contract)
        self.assertEqual(payslip.struct_id, self.structure)
        self.assertEqual(payslip.employee_id.name, 'Jared')

        cats = self._getCategories(payslip)
        self.assertEqual(cats['GROSS'], 7000.0)
        self.assertEqual(cats['EE_CA_FIT'], -1022.02)  # amount from apps.cra-arc.gc.ca
        self.assertEqual(cats['EE_CA_PIT'], -538.59)  # amount from apps.cra-arc.gc.ca

    # def test_tax_quebec(self):
    #     salary = 7000.0
    #     date_from = '2021-01-01'
    #     date_to = '2021-01-31'
    #
    #     employee = self._createEmployee()
    #     contract = self._createContract(employee,
    #                                     wage=salary,
    #                                     state_id=self.get_ca_state('QC'))
    #
    #
    #     self._log('2021 tax first payslip:')
    #     payslip = self._createPayslip(employee, date_from, date_to)
    #     # self.assertEqual(payslip.struct_type_id, )
    #     self.assertEqual(payslip.contract_id, contract)
    #     self.assertEqual(payslip.struct_id, self.structure)
    #     self.assertEqual(payslip.employee_id.name, 'Jared')
    #
    #     cats = self._getCategories(payslip)
    #     self.assertEqual(cats['GROSS'], 7000.0)
    #     self.assertEqual(cats['EE_CA_FIT'], -849.08)  # amount from apps.cra-arc.gc.ca
    #     self.assertEqual(cats['EE_CA_PIT'], -538.59)
