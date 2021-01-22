from odoo import fields, models


class WebsiteConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_deposit_threshold = fields.Monetary(string="Payment Deposit Threshold",
                                                related="website_id.payment_deposit_threshold",
                                                readonly=False)
