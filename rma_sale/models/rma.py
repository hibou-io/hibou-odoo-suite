# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_protected_fields(self):
        res = super(SaleOrderLine, self)._get_protected_fields()
        context = self._context or {}
        if context.get('rma_done'):
            if 'product_uom_qty' in res:
                res.remove('product_uom_qty')
            # technically used by product_cores to update related core pieces
            if 'product_id' in res:
                res.remove('product_id')
            if 'product_uom' in res:
                res.remove('product_uom')
        return res


class RMATemplate(models.Model):
    _inherit = 'rma.template'

    usage = fields.Selection(selection_add=[('sale_order', 'Sale Order')])
    sale_order_warranty = fields.Boolean(string='Sale Order Warranty',
                                         help='Determines if the regular return validity or '
                                              'Warranty validity is used.')
    so_decrement_order_qty = fields.Boolean(string='SO Decrement Ordered Qty.',
                                            help='When completing the RMA, the Ordered Quantity will be decremented by '
                                                 'the RMA qty.')

    def _portal_try_create(self, request_user, res_id, **kw):
        if self.usage == 'sale_order':
            prefix = 'line_'
            line_map = {int(key[len(prefix):]): float(kw[key]) for key in kw if key.find(prefix) == 0 and kw[key]}
            if line_map:
                sale_order = self.env['sale.order'].with_user(request_user).browse(res_id)
                if not sale_order.exists():
                    raise ValidationError(_('Invalid user for sale order.'))
                lines = []
                sale_order_sudo = sale_order.sudo()
                for line_id, qty in line_map.items():
                    line = sale_order_sudo.order_line.filtered(lambda l: l.id == line_id)
                    if line:
                        if not qty:
                            continue
                        if qty < 0.0 or line.qty_delivered < qty:
                            raise ValidationError(_('Invalid quantity.'))
                        validity = self._rma_sale_line_validity(line)
                        if not validity:
                            raise ValidationError(_('Product is not eligible for return.'))
                        if validity == 'expired':
                            raise ValidationError(_('Product is past the return period.'))
                        lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'sale_line_id': line.id,
                            'product_uom_id': line.product_uom.id,
                            'product_uom_qty': qty,
                        }))
                if not lines:
                    raise ValidationError(_('Missing product quantity.'))
                rma = self.env['rma.rma'].create({
                    'name': _('New'),
                    'sale_order_id': sale_order.id,
                    'template_id': self.id,
                    'partner_id': sale_order.partner_id.id,
                    'partner_shipping_id': sale_order.partner_shipping_id.id,
                    'lines': lines,
                })
                return rma
        return super(RMATemplate, self)._portal_try_create(request_user, res_id, **kw)

    def _portal_template(self, res_id=None):
        if self.usage == 'sale_order':
            return 'rma_sale.portal_new_sale_order'
        return super(RMATemplate, self)._portal_template(res_id=res_id)

    def _portal_values(self, request_user, res_id=None):
        if self.usage == 'sale_order':
            sale_orders = None
            sale_order = None
            if res_id:
                sale_order = self.env['sale.order'].with_user(request_user).browse(res_id)
                if sale_order:
                    sale_order = sale_order.sudo()
            else:
                sale_orders = self.env['sale.order'].with_user(request_user).search([], limit=100)
            return {
                'rma_template': self,
                'rma_sale_orders': sale_orders,
                'rma_sale_order': sale_order,
            }
        return super(RMATemplate, self)._portal_values(request_user, res_id=res_id)

    def _rma_sale_line_validity(self, so_line):
        if self.sale_order_warranty:
            validity_days = so_line.product_id.rma_sale_warranty_validity
        else:
            validity_days = so_line.product_id.rma_sale_validity
        if validity_days < 0:
            return ''
        elif validity_days > 0:
            sale_date = so_line.order_id.date_order
            now = fields.Datetime.now()
            if sale_date < (now - timedelta(days=validity_days)):
                return 'expired'
        return 'valid'
    
    def _values_for_in_picking(self, rma):
        values = super()._values_for_in_picking(rma)
        if self.usage == 'sale_order':
            values['move_lines'] = [(0, None, {
                'name': rma.name + ' IN: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.in_procure_method,
                'to_refund': self.in_to_refund,
                'location_id': self.in_location_id.id,
                'location_dest_id': self.in_location_dest_id.id,
                'sale_line_id': l.sale_line_id.id,
            }) for l in rma.lines.filtered(lambda l: l.product_id.type != 'service')]
        return values

    def _values_for_out_picking(self, rma):
        values = super()._values_for_out_picking(rma)
        if self.usage == 'sale_order':
            values['move_lines'] = [(0, None, {
                'name': rma.name + ' OUT: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.out_procure_method,
                'to_refund': self.out_to_refund,
                'location_id': self.out_location_id.id,
                'location_dest_id': self.out_location_dest_id.id,
                'sale_line_id': l.sale_line_id.id,
            }) for l in rma.lines.filtered(lambda l: l.product_id.type != 'service')]
        return values


class RMA(models.Model):
    _inherit = 'rma.rma'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_rma_count = fields.Integer('Number of RMAs for this Sale Order', compute='_compute_sale_order_rma_count')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company)

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
            else:
                rma.sale_order_rma_count = 0.0

    def open_sale_order_rmas(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order RMAs'),
            'res_model': 'rma.rma',
            'view_mode': 'tree,form',
            'context': {'search_default_sale_order_id': self[0].sale_order_id.id}
        }

    @api.onchange('template_usage')
    def _onchange_template_usage(self):
        res = super(RMA, self)._onchange_template_usage()
        for rma in self.filtered(lambda rma: rma.template_usage != 'sale_order'):
            rma.sale_order_id = False
        return res

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        for rma in self.filtered(lambda rma: rma.sale_order_id):
            rma.partner_id = rma.sale_order_id.partner_id
            rma.partner_shipping_id = rma.sale_order_id.partner_shipping_id

    def action_done(self):
        res = super(RMA, self).action_done()
        res2 = self._so_action_done()
        if isinstance(res, dict) and isinstance(res2, dict):
            if 'warning' in res and 'warning' in res2:
                res['warning'] = '\n'.join([res['warning'], res2['warning']])
                return res
            if 'warning' in res2:
                res['warning'] = res2['warning']
                return res
        elif isinstance(res2, dict):
            return res2
        return res

    def _so_action_done(self):
        warnings = []
        for rma in self:
            if rma.template_id.so_decrement_order_qty:
                for rma_line in rma.lines:
                    sale_line = rma_line.sale_line_id
                    if sale_line:
                        sale_line_qty = sale_line.product_uom_qty - rma_line.product_uom_qty
                        if sale_line_qty < 0:
                            warnings.append((rma, rma.sale_order_id, rma_line, abs(sale_line_qty)))
                            sale_line_qty = 0
                        sale_line.with_context(rma_done=True).write({'product_uom_qty': sale_line_qty})
            # Try to invoice if we don't already have an invoice (e.g. from resetting to draft)
            if rma.sale_order_id and rma.template_id.invoice_done and not rma.invoice_ids:
                rma.invoice_ids |= rma._sale_invoice_done(rma.sale_order_id)
        if warnings:
            return {'warning': _('Could not reduce all ordered qty:\n %s' % '\n'.join(
                ['%s %s %s : %s' % (w[0].name, w[1].name, w[2].product_id.display_name, w[3]) for w in warnings]))}
        return True

    def _sale_invoice_done(self, sale_orders):
        original_invoices = sale_orders.mapped('invoice_ids')
        try:
            wiz = self.env['sale.advance.payment.inv'].with_context(active_ids=sale_orders.ids).create({})
            wiz.create_invoices()
        except UserError:
            pass
        return sale_orders.mapped('invoice_ids') - original_invoices

    def _invoice_values_sale_order(self):
        # the RMA invoice API will not be used as invoicing will happen at the SO level
        return False

    def action_add_so_lines(self):
        make_line_obj = self.env['rma.sale.make.lines']
        for rma in self:
            lines = make_line_obj.create({
                'rma_id': rma.id,
            })
            action = self.env['ir.actions.act_window']._for_xml_id('rma_sale.action_rma_add_lines')
            action['res_id'] = lines.id
            return action

    def _create_in_picking_sale_order(self):
        if not self.sale_order_id:
            raise UserError(_('You must have a sale order for this RMA.'))
        if not self.template_id.in_require_return:
            group_id = self.sale_order_id.procurement_group_id.id if self.sale_order_id.procurement_group_id else 0
            sale_id = self.sale_order_id.id
            values = self.template_id._values_for_in_picking(self)
            update = {'sale_id': sale_id, 'group_id': group_id}
            update_lines = {'to_refund': self.template_id.in_to_refund, 'group_id': group_id}
            return self._picking_from_values(values, update, update_lines)

        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1 and l.product_id.type != 'service')
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))
        product_ids = lines.mapped('product_id.id')

        old_picking = self._find_candidate_return_picking(product_ids, self.sale_order_id.picking_ids, self.template_id.in_location_id.id)
        if not old_picking:
            raise UserError(_('No eligible pickings were found to return (you can only return products from the same initial picking).'))

        new_picking = self._new_in_picking(old_picking)
        self._new_in_moves(old_picking, new_picking, {})
        return new_picking

    def _create_out_picking_sale_order(self):
        if not self.sale_order_id:
            raise UserError(_('You must have a sale order for this RMA.'))
        if not self.template_id.out_require_return:
            group_id = self.sale_order_id.procurement_group_id.id if self.sale_order_id.procurement_group_id else 0
            sale_id = self.sale_order_id.id
            values = self.template_id._values_for_out_picking(self)
            update = {'sale_id': sale_id, 'group_id': group_id}
            update_lines = {'group_id': group_id}
            return self._picking_from_values(values, update, update_lines)

        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1 and l.product_id.type != 'service')
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))
        product_ids = lines.mapped('product_id.id')

        old_picking = self._find_candidate_return_picking(product_ids, self.sale_order_id.picking_ids, self.template_id.out_location_dest_id.id)
        if not old_picking:
            raise UserError(_(
                'No eligible pickings were found to duplicate (you can only return products from the same initial picking).'))

        new_picking = self._new_out_picking(old_picking)
        self._new_out_moves(old_picking, new_picking, {})
        return new_picking
    
    def _get_old_move(self, old_picking, line):
        if self.template_usage != 'sale_order':
            return super(RMA, self)._get_old_move(old_picking, line)
        return old_picking.move_lines.filtered(
            lambda ol: ol.state == 'done' and 
                       ol.product_id == line.product_id and
                       ol.sale_line_id == line.sale_line_id
        )[0]


class RMALine(models.Model):
    _inherit = 'rma.line'
    
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    sale_line_product_uom_qty = fields.Float('Ordered', related='sale_line_id.product_uom_qty')
    sale_line_qty_delivered = fields.Float('Delivered', related='sale_line_id.qty_delivered')
    sale_line_qty_invoiced = fields.Float('Invoiced', related='sale_line_id.qty_invoiced')
