# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RMATemplate(models.Model):
    _inherit = 'rma.template'

    usage = fields.Selection(selection_add=[('sale_order', 'Sale Order')])


class RMA(models.Model):
    _inherit = 'rma.rma'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_rma_count = fields.Integer('Number of RMAs for this Sale Order', compute='_compute_sale_order_rma_count')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))

    @api.multi
    @api.depends('sale_order_id')
    def _compute_sale_order_rma_count(self):
        for rma in self:
            if rma.sale_order_id:
                rma_data = self.read_group([('sale_order_id', '=', rma.sale_order_id.id), ('state', '!=', 'cancel')],
                                           ['sale_order_id'], ['sale_order_id'])
                if rma_data:
                    rma.sale_order_rma_count = rma_data[0]['sale_order_id_count']
            else:
                rma.sale_order_rma_count = 0.0


    @api.multi
    def open_sale_order_rmas(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order RMAs'),
            'res_model': 'rma.rma',
            'view_mode': 'tree,form',
            'context': {'search_default_sale_order_id': self[0].sale_order_id.id}
        }

    @api.onchange('template_usage')
    @api.multi
    def _onchange_template_usage(self):
        res = super(RMA, self)._onchange_template_usage()
        for rma in self.filtered(lambda rma: rma.template_usage != 'sale_order'):
            rma.sale_order_id = False
        return res

    @api.onchange('sale_order_id')
    @api.multi
    def _onchange_sale_order_id(self):
        for rma in self.filtered(lambda rma: rma.sale_order_id):
            rma.partner_id = rma.sale_order_id.partner_id
            rma.partner_shipping_id = rma.sale_order_id.partner_shipping_id


    @api.multi
    def action_add_so_lines(self):
        make_line_obj = self.env['rma.sale.make.lines']
        for rma in self:
            lines = make_line_obj.create({
                'rma_id': rma.id,
            })
            action = self.env.ref('rma_sale.action_rma_add_lines').read()[0]
            action['res_id'] = lines.id
            return action

    def _create_in_picking_sale_order(self):
        if not self.sale_order_id:
            raise UserError(_('You must have a sale order for this RMA.'))
        if not self.template_id.in_require_return:
            group_id = self.sale_order_id.procurement_group_id.id if self.sale_order_id.procurement_group_id else 0
            sale_id = self.sale_order_id.id if self.sale_order_id else 0

            values = self.template_id._values_for_in_picking(self)
            values.update({'sale_id': sale_id, 'group_id': group_id})
            move_lines = []
            for l1, l2, vals in values['move_lines']:
                vals.update({'to_refund_so': self.template_id.in_to_refund_so, 'group_id': group_id})
                move_lines.append((l1, l2, vals))
            values['move_lines'] = move_lines
            return self.env['stock.picking'].sudo().create(values)

        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1)
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))
        product_ids = lines.mapped('product_id.id')

        old_picking = self._find_candidate_return_picking(product_ids, self.sale_order_id.picking_ids, self.template_id.in_location_id.id)
        if not old_picking:
            raise UserError('No eligible pickings were found to return (you can only return products from the same initial picking).')

        new_picking = old_picking.copy({
            'move_lines': [],
            'picking_type_id': self.template_id.in_type_id.id,
            'state': 'draft',
            'origin': old_picking.name + ' ' + self.name,
            'location_id': self.template_id.in_location_id.id,
            'location_dest_id': self.template_id.in_location_dest_id.id,
            'carrier_id': self.template_id.in_carrier_id.id if self.template_id.in_carrier_id else 0,
            'carrier_tracking_ref': False,
            'carrier_price': False
        })
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self},
            subtype_id=self.env.ref('mail.mt_note').id)

        for l in lines:
            return_move = old_picking.move_lines.filtered(lambda ol: ol.state == 'done' and ol.product_id.id == l.product_id.id)[0]
            return_move.copy({
                'name': self.name + ' IN: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'picking_id': new_picking.id,
                'state': 'draft',
                'location_id': return_move.location_dest_id.id,
                'location_dest_id': self.template_id.in_location_dest_id.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': new_picking.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': return_move.id,
                'procure_method': self.template_id.in_procure_method,
                'move_dest_id': False,
                'to_refund_so': self.template_id.in_to_refund_so,
            })

        return new_picking

    def _create_out_picking_sale_order(self):
        if not self.sale_order_id:
            raise UserError(_('You must have a sale order for this RMA.'))
        if not self.template_id.out_require_return:
            group_id = self.sale_order_id.procurement_group_id.id if self.sale_order_id.procurement_group_id else 0
            sale_id = self.sale_order_id.id if self.sale_order_id else 0

            values = self.template_id._values_for_out_picking(self)
            values.update({'sale_id': sale_id, 'group_id': group_id})
            move_lines = []
            for l1, l2, vals in values['move_lines']:
                vals.update({'group_id': group_id})
                move_lines.append((l1, l2, vals))
            values['move_lines'] = move_lines
            return self.env['stock.picking'].sudo().create(values)

        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1)
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))
        product_ids = lines.mapped('product_id.id')

        old_picking = self._find_candidate_return_picking(product_ids, self.sale_order_id.picking_ids, self.template_id.out_location_dest_id.id)
        if not old_picking:
            raise UserError(
                'No eligible pickings were found to duplicate (you can only return products from the same initial picking).')

        new_picking = old_picking.copy({
            'move_lines': [],
            'picking_type_id': self.template_id.out_type_id.id,
            'state': 'draft',
            'origin': old_picking.name + ' ' + self.name,
            'location_id': self.template_id.out_location_id.id,
            'location_dest_id': self.template_id.out_location_dest_id.id,
            'carrier_id': self.template_id.out_carrier_id.id if self.template_id.out_carrier_id else 0,
            'carrier_tracking_ref': False,
            'carrier_price': False
        })
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        for l in lines:
            return_move = old_picking.move_lines.filtered(lambda ol: ol.state == 'done' and ol.product_id.id == l.product_id.id)[0]
            return_move.copy({
                'name': self.name + ' OUT: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'picking_id': new_picking.id,
                'state': 'draft',
                'location_id': self.template_id.out_location_id.id,
                'location_dest_id': self.template_id.out_location_dest_id.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': new_picking.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': False,
                'procure_method': self.template_id.out_procure_method,
                'move_dest_id': False,
            })

        return new_picking


