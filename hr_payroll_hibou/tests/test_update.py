import datetime

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestUpdate(common.TransactionCase):
    
    def setUp(self):
        super().setUp()
        # setup the database to run in general
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        self.param_model = self.env['ir.config_parameter'].sudo()
        self.param_model.set_param('database.hibou_professional_expiration_date', fields.Date.to_string(tomorrow))
        self.param_model.set_param('database.hibou_professional_code', 'TESTCODE')
    
    def test_01_database_state(self):
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)
        self.param_model.set_param('database.hibou_professional_expiration_date', fields.Date.to_string(yesterday))
        
        update = self.env['hr.payroll.publisher.update']\
            .with_context(test_payroll_update_result='{"payroll_parameter_values":[]}')\
            .create({
            'request_modules': 'test',
        })
        self.assertEqual(update.state, 'draft')
        update.button_send()
        self.assertEqual(update.state, 'error')
        
        self.param_model.set_param('database.hibou_professional_expiration_date', fields.Date.to_string(tomorrow))
        update.button_send()
        self.assertEqual(update.state, 'done')
        self.assertEqual(update.parameter_codes_retrieved, '')
        
        # Reset to a degree.
        update = update.with_context(test_payroll_update_result='{"payroll_parameter_values":[["missing_code", "2021-01-01", "5.0"]]}')
        update.write({
            'state': 'draft',
            'result': '',
        })
        update.button_send()
        self.assertEqual(update.state, 'done')
        self.assertEqual(update.parameter_codes_retrieved, 'missing_code (MISSING)')

        # Actually add to a rule.
        test_parameter = self.env['hr.rule.parameter'].create({
            'code': 'test_parameter_1',
            'name': 'Test Parameter 1',
        })
        update = update.with_context(test_payroll_update_result='{"payroll_parameter_values":[["test_parameter_1", "2021-01-01", "5.0"]]}')
        update.write({
            'state': 'draft',
            'result': '',
        })
        update.button_send()
        self.assertEqual(update.state, 'done')
        self.assertEqual(update.parameter_codes_retrieved, 'test_parameter_1')
        self.assertTrue(test_parameter.parameter_version_ids)
        self.assertEqual(test_parameter.parameter_version_ids.parameter_value, '5.0')
        self.assertEqual(str(test_parameter.parameter_version_ids.date_from), '2021-01-01')
        
        test_parameter.parameter_version_ids.write({
            'parameter_value': '',
        })
        self.assertEqual(test_parameter.parameter_version_ids.parameter_value, '')
        update.write({
            'state': 'draft',
            'result': '',
        })
        update.button_send()
        # doesn't make a new one, updates existing...
        self.assertEqual(test_parameter.parameter_version_ids.parameter_value, '5.0')
        
        # Test that we can lock the parameter
        test_parameter.parameter_version_ids.write({
            'parameter_value': 'locked',
        })
        test_parameter.write({
            'update_locked': True,
        })
        self.assertEqual(test_parameter.parameter_version_ids.parameter_value, 'locked')
        update.write({
            'state': 'draft',
            'result': '',
        })
        update.button_send()
        # doesn't make a new one, updates existing...
        self.assertEqual(test_parameter.parameter_version_ids.parameter_value, 'locked')
        self.assertEqual(update.parameter_codes_retrieved, 'test_parameter_1 (LOCKED)')
