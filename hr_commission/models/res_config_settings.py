# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_journal_id = fields.Many2one(related='company_id.commission_journal_id', readonly=False)
    commission_liability_id = fields.Many2one(related='company_id.commission_liability_id', readonly=False)
    commission_type = fields.Selection(related='company_id.commission_type', readonly=False)
    commission_amount_type = fields.Selection(related='company_id.commission_amount_type', readonly=False)
