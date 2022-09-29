# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_journal_id = fields.Many2one(related='company_id.commission_journal_id', readonly=False)
    commission_liability_id = fields.Many2one(related='company_id.commission_liability_id', readonly=False)
    commission_type = fields.Selection(related='company_id.commission_type', readonly=False)
    commission_amount_type = fields.Selection(related='company_id.commission_amount_type', readonly=False)
    commission_margin_threshold = fields.Float()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        margin_threshold = float(self.env['ir.config_parameter'].sudo().get_param('commission.margin.threshold', default=0.0))
        res.update(commission_margin_threshold=margin_threshold)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('commission.margin.threshold', self.commission_margin_threshold)
