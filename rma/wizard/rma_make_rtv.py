# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class RMAMakeRTV(models.TransientModel):
    _name = 'rma.make.rtv'
    _description = 'Make RTV Batch'

    partner_id = fields.Many2one('res.partner', string='Vendor')
    partner_shipping_id = fields.Many2one('res.partner', string='Shipping Address')
    rma_line_ids = fields.One2many('rma.make.rtv.line', 'rma_make_rtv_id', string='Lines')

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        if 'rma_line_ids' in fields and self._context.get('active_model') == 'rma.rma' and self._context.get('active_ids'):
            active_ids = self._context.get('active_ids')
            rmas = self.env['rma.rma'].browse(active_ids)
            result['rma_line_ids'] = [(0, 0, {
                'rma_id': r.id,
                'rma_state': r.state,
                'rma_claim_number': r.claim_number,
            }) for r in rmas]
            rma_partner = rmas.mapped('partner_id')
            if rma_partner:
                result['partner_id'] = rma_partner[0].id
        return result

    def create_batch(self):
        self.ensure_one()
        if self.rma_line_ids.filtered(lambda rl: rl.rma_id.state != 'draft'):
            raise UserError('All RMAs must be in the draft state.')
        rma_partner = self.rma_line_ids.mapped('rma_id.partner_id')
        if rma_partner and len(rma_partner) != 1:
            raise UserError('All RMAs must be for the same partner.')
        elif not rma_partner and not self.partner_id:
            raise UserError('Please select a Vendor')
        elif not rma_partner:
            rma_partner = self.partner_id
            rma_partner_shipping = self.partner_shipping_id or rma_partner
            # update all RMA's to the currently selected vendor
            self.rma_line_ids.mapped('rma_id').write({
                'partner_id': rma_partner.id,
                'partner_shipping_id': rma_partner_shipping.id,
            })
        if len(self.rma_line_ids.mapped('rma_id.template_id')) != 1:
            raise UserError('All RMAs must be of the same template.')

        in_values = None
        out_values = None
        for rma in self.rma_line_ids.mapped('rma_id'):
            if rma.template_id.create_in_picking:
                if not in_values:
                    in_values = rma.template_id._values_for_in_picking(rma)
                    in_values['origin'] = [in_values['origin']]
                else:
                    other_in_values = rma.template_id._values_for_in_picking(rma)
                    in_values['move_lines'] += other_in_values['move_lines']
            if rma.template_id.create_out_picking:
                if not out_values:
                    out_values = rma.template_id._values_for_out_picking(rma)
                    out_values['origin'] = [out_values['origin']]
                else:
                    other_out_values = rma.template_id._values_for_out_picking(rma)
                    out_values['move_lines'] += other_out_values['move_lines']
        in_picking_id = False
        out_picking_id = False
        if in_values:
            in_values['origin'] = ', '.join(in_values['origin'])
            in_picking = self.env['stock.picking'].sudo().create(in_values)
            in_picking_id = in_picking.id
        if out_values:
            out_values['origin'] = ', '.join(out_values['origin'])
            out_picking = self.env['stock.picking'].sudo().create(out_values)
            out_picking_id = out_picking.id
        rmas = self.rma_line_ids.mapped('rma_id').with_context(rma_in_picking_id=in_picking_id, rma_out_picking_id=out_picking_id)
        # action_confirm known to be multi-aware and makes only one context
        rmas.action_confirm()


class RMAMakeRTVLine(models.TransientModel):
    _name = 'rma.make.rtv.line'
    _description = 'Make RTV Batch RMA'

    rma_make_rtv_id = fields.Many2one('rma.make.rtv')
    rma_id = fields.Many2one('rma.rma')
    rma_state = fields.Selection(related='rma_id.state')
    rma_claim_number = fields.Char(related='rma_id.claim_number', readonly=False)
