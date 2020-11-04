from odoo import api, models, fields


class Ticket(models.Model):
    _inherit = 'helpdesk.ticket'

    sale_order_count = fields.Integer(related='partner_id.sale_order_count', string='# of Sale Orders')

    def action_partner_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.act_res_partner_2_sale_order').read()[0]
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
        }
        return action
