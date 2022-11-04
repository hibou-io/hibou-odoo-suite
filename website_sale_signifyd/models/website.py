# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    signifyd_connector_id = fields.Many2one('signifyd.connector', ondelete='set null')
