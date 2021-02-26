from odoo import fields
from odoo.tests.common import Form, TransactionCase


class TestPartnerZip(TransactionCase):
    def test_00_onchange_zip(self):
        country_us = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        state_wa = self.env['res.country.state'].search([('code', '=', 'WA'),
                                                         ('country_id', '=', country_us.id),
                                                         ], limit=1)

        f = Form(self.env['res.partner'])
        self.assertFalse(f.city)
        self.assertFalse(f.state_id)
        self.assertFalse(f.country_id)
        self.assertFalse(f.zip)
        if hasattr(f, 'partner_latitude'):
            self.assertFalse(f.partner_latitude)
            self.assertFalse(f.partner_longitude)
            self.assertFalse(f.date_localization)

        f.zip = '98270'
        f.name = 'Required Field'
        p = f.save()
        self.assertEqual(p.city, 'Marysville')
        self.assertEqual(p.state_id, state_wa)
        self.assertEqual(p.country_id, country_us)
        if hasattr(p, 'partner_latitude'):
            self.assertEqual(p.partner_latitude, 48.06)
            self.assertEqual(p.partner_longitude, -122.16)
            self.assertEqual(p.date_localization, fields.Date.context_today(p))
