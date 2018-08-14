# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..controllers.main import create_hmac
from datetime import timedelta, datetime
from time import mktime


class RMATemplate(models.Model):
    _name = 'rma.template'

    name = fields.Char(string='Name')
    usage = fields.Selection([], string='Applies To')
    description = fields.Html(string='Internal Instructions')
    customer_description = fields.Html(string='Customer Instructions')
    valid_days = fields.Integer(string='Expire in Days')

    create_in_picking = fields.Boolean(string='Create Inbound Picking')
    create_out_picking = fields.Boolean(string='Create Outbound Picking')

    in_type_id = fields.Many2one('stock.picking.type', string='Inbound Picking Type')
    out_type_id = fields.Many2one('stock.picking.type', string='Outbound Picking Type')

    in_location_id = fields.Many2one('stock.location', string='Inbound Source Location')
    in_location_dest_id = fields.Many2one('stock.location', string='Inbound Destination Location')
    in_carrier_id = fields.Many2one('delivery.carrier', string='Inbound Carrier')
    in_require_return = fields.Boolean(string='Inbound Require return of picking')
    in_procure_method = fields.Selection([
        ('make_to_stock', 'Take from Stock'),
        ('make_to_order', 'Apply Procurements')
        ], string="Inbound Procurement Method", default='make_to_stock')
    in_to_refund_so = fields.Boolean(string='Inbound mark refund SO')

    out_location_id = fields.Many2one('stock.location', string='Outbound Source Location')
    out_location_dest_id = fields.Many2one('stock.location', string='Outbound Destination Location')
    out_carrier_id = fields.Many2one('delivery.carrier', string='Outbound Carrier')
    out_require_return = fields.Boolean(string='Outbound Require picking to duplicate')
    out_procure_method = fields.Selection([
        ('make_to_stock', 'Take from Stock'),
        ('make_to_order', 'Apply Procurements')
        ], string="Outbound Procurement Method", default='make_to_stock')

    def _values_for_in_picking(self, rma):
        return {
            'origin': rma.name,
            'partner_id': rma.partner_shipping_id.id,
            'picking_type_id': self.in_type_id.id,
            'location_id': self.in_location_id.id,
            'location_dest_id': self.in_location_dest_id.id,
            'carrier_id': self.in_carrier_id.id if self.in_carrier_id else False,
            'move_lines': [(0, None, {
                'name': rma.name + ' IN: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.in_procure_method,
            }) for l in rma.lines],
        }

    def _values_for_out_picking(self, rma):
        return {
            'origin': rma.name,
            'partner_id': rma.partner_shipping_id.id,
            'picking_type_id': self.out_type_id.id,
            'location_id': self.out_location_id.id,
            'location_dest_id': self.out_location_dest_id.id,
            'carrier_id': self.out_carrier_id.id if self.out_carrier_id else False,
            'move_lines': [(0, None, {
                'name': rma.name + ' OUT: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.out_procure_method,
            }) for l in rma.lines],
        }


class RMATag(models.Model):
    _name = "rma.tag"
    _description = "RMA Tag"

    name = fields.Char('Tag Name', required=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class RMA(models.Model):
    _name = 'rma.rma'
    _inherit = ['mail.thread']
    _description = 'RMA'
    _order = 'id desc'

    name = fields.Char(string='Number', copy=False)
    state = fields.Selection([
            ('draft', 'New'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='State', default='draft', copy=False)
    company_id = fields.Many2one('res.company', 'Company')
    template_id = fields.Many2one('rma.template', string='Type', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_shipping_id = fields.Many2one('res.partner', string='Shipping')
    lines = fields.One2many('rma.line', 'rma_id', string='Lines')
    tag_ids = fields.Many2many('rma.tag', 'rma_tags_rel', 'rma_id', 'tag_id', string='Tags')
    description = fields.Html(string='Internal Instructions', related='template_id.description')
    customer_description = fields.Html(string='Customer Instructions', related='template_id.customer_description')
    template_usage = fields.Selection(string='Template Usage', related='template_id.usage')
    validity_date = fields.Datetime(string='Expiration Date')

    in_picking_id = fields.Many2one('stock.picking', string='Inbound Picking', copy=False)
    out_picking_id = fields.Many2one('stock.picking', string='Outbound Picking', copy=False)

    in_picking_state = fields.Selection(string='In Picking State', related='in_picking_id.state')
    out_picking_state = fields.Selection(string='Out Picking State', related='out_picking_id.state')

    in_picking_carrier_id = fields.Many2one('delivery.carrier', related='in_picking_id.carrier_id')
    out_picking_carrier_id = fields.Many2one('delivery.carrier', related='out_picking_id.carrier_id')

    in_carrier_tracking_ref = fields.Char(related='in_picking_id.carrier_tracking_ref')
    in_label_url = fields.Char(compute='_compute_in_label_url')
    out_carrier_tracking_ref = fields.Char(related='out_picking_id.carrier_tracking_ref')


    @api.onchange('template_usage')
    @api.multi
    def _onchange_template_usage(self):
        now = datetime.now()
        for rma in self.filtered(lambda r: r.template_id.valid_days):
            rma.validity_date = now + timedelta(days=rma.template_id.valid_days)


    @api.onchange('in_carrier_tracking_ref', 'validity_date')
    @api.multi
    def _compute_in_label_url(self):
        config = self.env['ir.config_parameter'].sudo()
        secret = config.search([('key', '=', 'database.secret')], limit=1)
        secret = str(secret.value) if secret else ''
        base_url = config.search([('key', '=', 'web.base.url')], limit=1)
        base_url = str(base_url.value) if base_url else ''
        for rma in self:
            if not rma.in_picking_id:
                rma.in_label_url = ''
                continue
            if rma.validity_date:
                e_expires = int(mktime(fields.Datetime.from_string(rma.validity_date).timetuple()))
            else:
                year = datetime.now() + timedelta(days=365)
                e_expires = int(mktime(year.timetuple()))
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', rma.in_picking_id.id),
                ('name', 'like', 'Label%')], limit=1)
            if not attachment:
                rma.in_label_url = ''
                continue
            rma.in_label_url = base_url + '/rma_label?a=' + \
                str(attachment.id) + '&e=' + str(e_expires) + \
                '&h=' + create_hmac(secret, attachment.id, e_expires)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('rma.rma') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.rma') or _('New')

        result = super(RMA, self).create(vals)
        return result

    @api.multi
    def action_confirm(self):
        for rma in self:
            in_picking_id = False
            out_picking_id = False
            if any((not rma.template_id, not rma.lines, not rma.partner_id, not rma.partner_shipping_id)):
                raise UserError(_('You can only confirm RMAs with lines, and partner information.'))
            if rma.template_id.create_in_picking:
                in_picking_id = rma._create_in_picking()
                if in_picking_id:
                    in_picking_id.action_confirm()
                    in_picking_id.action_assign()
            if rma.template_id.create_out_picking:
                out_picking_id = rma._create_out_picking()
                if out_picking_id:
                    out_picking_id.action_confirm()
                    out_picking_id.action_assign()
            rma.write({'state': 'confirmed',
                       'in_picking_id': in_picking_id.id if in_picking_id else False,
                       'out_picking_id': out_picking_id.id if out_picking_id else False})

    @api.multi
    def action_done(self):
        for rma in self:
            if rma.in_picking_id and rma.in_picking_id.state not in ('done', 'cancel'):
                raise UserError(_('Inbound picking not complete or cancelled.'))
            if rma.out_picking_id and rma.out_picking_id.state not in ('done', 'cancel'):
                raise UserError(_('Outbound picking not complete or cancelled.'))
        self.write({'state': 'done'})

    @api.multi
    def action_cancel(self):
        for rma in self:
            rma.in_picking_id.action_cancel()
            rma.out_picking_id.action_cancel()
        self.write({'state': 'cancel'})

    @api.multi
    def action_draft(self):
        self.filtered(lambda l: l.state == 'cancel').write({
            'state': 'draft', 'in_picking_id': False, 'out_picking_id': False})

    @api.multi
    def _create_in_picking(self):
        if self.template_usage and hasattr(self, '_create_in_picking_' + self.template_usage):
            return getattr(self, '_create_in_picking_' + self.template_usage)()
        values = self.template_id._values_for_in_picking(self)
        return self.env['stock.picking'].sudo().create(values)

    def _create_out_picking(self):
        if self.template_usage and hasattr(self, '_create_out_picking_' + self.template_usage):
            return getattr(self, '_create_out_picking_' + self.template_usage)()
        values = self.template_id._values_for_out_picking(self)
        return self.env['stock.picking'].sudo().create(values)

    def _find_candidate_return_picking(self, product_ids, pickings, location_id):
        done_pickings = pickings.filtered(lambda p: p.state == 'done' and p.location_dest_id.id == location_id)
        for p in done_pickings:
            p_product_ids = p.move_lines.filtered(lambda l: l.state == 'done').mapped('product_id.id')
            if set(product_ids) & set(p_product_ids) == set(product_ids):
                return p
        return None

    @api.multi
    def action_in_picking_send_to_shipper(self):
        for rma in self:
            if rma.in_picking_id and rma.in_picking_carrier_id:
                rma.in_picking_id.send_to_shipper()

    @api.multi
    def unlink(self):
        for rma in self:
            if rma.state not in ('draft'):
                raise UserError(_('You can not delete a non-draft RMA.'))
        return super(RMA, self).unlink()


class RMALine(models.Model):
    _name = 'rma.line'

    rma_id = fields.Many2one('rma.rma', string='RMA')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'UOM')
    product_uom_qty = fields.Float(string='QTY')
    rma_template_usage = fields.Selection(related='rma_id.template_usage')

    @api.onchange('product_id')
    @api.multi
    def _onchange_product_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id
