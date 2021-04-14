from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    signifyd_connector_id = fields.Many2one('signifyd.connector')
