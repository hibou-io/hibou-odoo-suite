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
            .with_context(test_payroll_update_result='{"payroll_parameter_values":[]}').create({
            'request_modules': 'test',
        })
        self.assertEqual(update.state, 'draft')
        update.button_send()
        self.assertEqual(update.state, 'error')
        
        self.param_model.set_param('database.hibou_professional_expiration_date', fields.Date.to_string(tomorrow))
        update.button_send()
        self.assertEqual(update.state, 'done')
