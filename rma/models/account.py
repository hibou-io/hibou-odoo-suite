# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    rma_ids = fields.Many2many('rma.rma',
                               'rma_invoice_rel',
                               'invoice_id',
                               'rma_id',
                               string='RMAs')
