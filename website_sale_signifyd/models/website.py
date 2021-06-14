from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    signifyd_connector_id = fields.Many2one('signifyd.connector')
