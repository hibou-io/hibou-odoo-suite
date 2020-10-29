from odoo import api, models, fields

from logging import getLogger
_logger = getLogger(__name__)


class Ticket(models.Model):
    _inherit = 'helpdesk.ticket'

    rma_count = fields.Integer(compute='_compute_rma_count')

    def _compute_rma_count(self):
        for ticket in self:
            if ticket.partner_id:
                ticket.rma_count = self.env['rma.rma'].search_count([('partner_id', 'child_of', ticket.partner_id.id)])
            else:
                ticket.rma_count = 0

    def action_partner_rma(self):
        self.ensure_one()
        action = self.env.ref('rma.action_rma_rma').read()[0]

        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
        }
        return action
