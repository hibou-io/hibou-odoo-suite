# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from ..controllers.main import create_hmac
from datetime import timedelta, datetime
from time import mktime


class RMATemplate(models.Model):
    _name = 'rma.template'
    _description = 'RMA Template'

    name = fields.Char(string='Name')
    usage = fields.Selection([
        ('stock_picking', 'Stock Picking'),
    ], string='Applies To')
    description = fields.Html(string='Internal Instructions')
    customer_description = fields.Html(string='Customer Instructions')
    valid_days = fields.Integer(string='Expire in Days')
    automatic_expire = fields.Boolean('Automatic Expire',
                                      help='RMAs with this template will automatically '
                                           'expire when past their expiration date.')
    invoice_done = fields.Boolean(string='Invoice on Completion')

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
    in_to_refund = fields.Boolean(string='Inbound Mark Refund')

    out_location_id = fields.Many2one('stock.location', string='Outbound Source Location')
    out_location_dest_id = fields.Many2one('stock.location', string='Outbound Destination Location')
    out_carrier_id = fields.Many2one('delivery.carrier', string='Outbound Carrier')
    out_require_return = fields.Boolean(string='Outbound Require picking to duplicate')
    out_procure_method = fields.Selection([
        ('make_to_stock', 'Take from Stock'),
        ('make_to_order', 'Apply Procurements')
        ], string="Outbound Procurement Method", default='make_to_stock')
    out_to_refund = fields.Boolean(string='Outbound Mark Refund')
    portal_ok = fields.Boolean(string='Allow on Portal')
    company_id = fields.Many2one('res.company', 'Company')
    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users',
                                            help='Users that get activities when creating RMA.')

    def _portal_try_create(self, request_user, res_id, **kw):
        if self.usage == 'stock_picking':
            prefix = 'move_'
            move_map = {int(key[len(prefix):]): float(kw[key]) for key in kw if key.find(prefix) == 0 and kw[key]}
            if move_map:
                picking = self.env['stock.picking'].browse(res_id)
                if picking.partner_id != request_user.partner_id:
                    raise ValidationError('Invalid user for picking.')
                lines = []
                for move_id, qty in move_map.items():
                    move = picking.move_lines.filtered(lambda l: l.id == move_id)
                    if move:
                        if not qty:
                            continue
                        if qty < 0.0 or move.quantity_done < qty:
                            raise ValidationError('Invalid quantity.')
                        lines.append((0, 0, {
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'product_uom_qty': qty,
                        }))
                if not lines:
                    raise ValidationError('Missing product quantity.')
                rma = self.env['rma.rma'].create({
                    'name': _('New'),
                    'stock_picking_id': picking.id,
                    'template_id': self.id,
                    'partner_id': request_user.partner_id.id,
                    'partner_shipping_id': request_user.partner_id.id,
                    'lines': lines,
                })
                return rma

    def _portal_template(self, res_id=None):
        if self.usage == 'stock_picking':
            return 'rma.portal_new_stock_picking'

    def _portal_values(self, request_user, res_id=None):
        if self.usage == 'stock_picking':
            picking = None
            pickings = None
            if res_id:
                picking = self.env['stock.picking'].browse(res_id)
                if picking.partner_id != request_user.partner_id:
                    picking = None
            else:
                pickings = self.env['stock.picking'].search([('partner_id', '=', request_user.partner_id.id)], limit=100)
            return {
                'rma_template': self,
                'pickings': pickings,
                'picking': picking,
            }

    def _values_for_in_picking(self, rma):
        return {
            'origin': rma.name,
            'partner_id': rma.partner_shipping_id.id,
            'picking_type_id': self.in_type_id.id,
            'location_id': self.in_location_id.id,
            'location_dest_id': self.in_location_dest_id.id,
            'carrier_id': rma.initial_in_picking_carrier_id.id,
            'move_lines': [(0, None, {
                'name': rma.name + ' IN: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.in_procure_method,
                'to_refund': self.in_to_refund,
            }) for l in rma.lines.filtered(lambda l: l.product_id.type != 'service')],
        }

    def _values_for_out_picking(self, rma):
        return {
            'origin': rma.name,
            'partner_id': rma.partner_shipping_id.id,
            'picking_type_id': self.out_type_id.id,
            'location_id': self.out_location_id.id,
            'location_dest_id': self.out_location_dest_id.id,
            'carrier_id': rma.initial_out_picking_carrier_id.id,
            'move_lines': [(0, None, {
                'name': rma.name + ' OUT: ' + l.product_id.name_get()[0][1],
                'product_id': l.product_id.id,
                'product_uom_qty': l.product_uom_qty,
                'product_uom': l.product_uom_id.id,
                'procure_method': self.out_procure_method,
                'to_refund': self.out_to_refund,
            }) for l in rma.lines.filtered(lambda l: l.product_id.type != 'service')],
        }

    def _schedule_responsible_activities(self, rma):
        model_id = self.env['ir.model']._get(rma._name).id
        activity_to_write = []
        for user in self.responsible_user_ids:
            if rma.with_user(user).check_access_rights('read', raise_exception=False):
                activity_to_write.append((0, 0, {
                    'res_id': rma.id,
                    'res_model_id': model_id,
                    'summary': 'Review New RMA',
                    'activity_type_id': False,
                    'user_id': user.id,
                }))
        if activity_to_write:
            rma.write({
                'activity_ids': activity_to_write,
            })

    def _rma_expire(self):
        templates = self.sudo().search([('automatic_expire', '=', True)])
        if not templates:
            return True
        rmas = self.env['rma.rma'].sudo().search([
            ('template_id', 'in', templates.ids),
            ('state', 'in', ('draft', 'confirmed',)),
            ('validity_date', '<', fields.Datetime.now())
        ])
        if rmas:
            return rmas._action_expire()
        return True


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
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'RMA'
    _order = 'id desc'
    _mail_post_access = 'read'

    name = fields.Char(string='Number', copy=False)
    state = fields.Selection([
            ('draft', 'New'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('expired', 'Expired'),
            ('cancel', 'Cancelled'),
        ], string='State', default='draft', copy=False)
    company_id = fields.Many2one('res.company', 'Company')
    template_id = fields.Many2one('rma.template', string='Type', required=True)
    template_create_in_picking = fields.Boolean(related='template_id.create_in_picking')
    template_create_out_picking = fields.Boolean(related='template_id.create_out_picking')

    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking')
    stock_picking_rma_count = fields.Integer('Number of RMAs for this Picking', compute='_compute_stock_picking_rma_count')
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_shipping_id = fields.Many2one('res.partner', string='Shipping')
    lines = fields.One2many('rma.line', 'rma_id', string='Lines')
    tag_ids = fields.Many2many('rma.tag', 'rma_tags_rel', 'rma_id', 'tag_id', string='Tags')
    description = fields.Html(string='Internal Instructions', related='template_id.description')
    customer_description = fields.Html(string='Customer Instructions', related='template_id.customer_description')
    template_usage = fields.Selection(string='Template Usage', related='template_id.usage')
    validity_date = fields.Datetime(string='Expiration Date')
    invoice_ids = fields.Many2many('account.move',
                                   'rma_invoice_rel',
                                   'rma_id',
                                   'invoice_id',
                                   string='Invoices')

    initial_in_picking_carrier_id = fields.Many2one('delivery.carrier', string='In Delivery Method')
    initial_out_picking_carrier_id = fields.Many2one('delivery.carrier', string='Out Delivery Method')

    in_picking_id = fields.Many2one('stock.picking', string='Inbound Picking', copy=False)
    out_picking_id = fields.Many2one('stock.picking', string='Outbound Picking', copy=False)

    in_picking_state = fields.Selection(string='In Picking State', related='in_picking_id.state')
    out_picking_state = fields.Selection(string='Out Picking State', related='out_picking_id.state')

    in_picking_carrier_id = fields.Many2one('delivery.carrier', related='in_picking_id.carrier_id', readonly=False)
    out_picking_carrier_id = fields.Many2one('delivery.carrier', related='out_picking_id.carrier_id', readonly=False)

    in_carrier_tracking_ref = fields.Char(related='in_picking_id.carrier_tracking_ref')
    in_label_url = fields.Char(compute='_compute_in_label_url')
    out_carrier_tracking_ref = fields.Char(related='out_picking_id.carrier_tracking_ref')


    def _compute_access_url(self):
        super(RMA, self)._compute_access_url()
        for rma in self:
            rma.access_url = '/my/rma/%s' % (rma.id)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        for rma in self:
            rma.initial_in_picking_carrier_id = rma.template_id.in_carrier_id
            rma.initial_out_picking_carrier_id = rma.template_id.out_carrier_id

    @api.onchange('template_usage')
    def _onchange_template_usage(self):
        now = datetime.now()
        for rma in self:
            if rma.template_id.valid_days:
                rma.validity_date = now + timedelta(days=rma.template_id.valid_days)
            if rma.template_usage != 'stock_picking':
                rma.stock_picking_id = False

    @api.onchange('stock_picking_id')
    def _onchange_stock_picking_id(self):
        for rma in self.filtered(lambda rma: rma.stock_picking_id):
            rma.partner_id = rma.stock_picking_id.partner_id
            rma.partner_shipping_id = rma.stock_picking_id.partner_id

    @api.onchange('in_carrier_tracking_ref', 'validity_date')
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

    @api.depends('stock_picking_id')
    def _compute_stock_picking_rma_count(self):
        for rma in self:
            if rma.stock_picking_id:
                rma_data = self.read_group([('stock_picking_id', '=', rma.stock_picking_id.id), ('state', '!=', 'cancel')],
                                           ['stock_picking_id'], ['stock_picking_id'])
                if rma_data:
                    rma.stock_picking_rma_count = rma_data[0]['stock_picking_id_count']
            else:
                rma.stock_picking_rma_count = 0.0

    def open_stock_picking_rmas(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Picking RMAs'),
            'res_model': 'rma.rma',
            'view_mode': 'tree,form',
            'context': {'search_default_stock_picking_id': self[0].stock_picking_id.id}
        }

    def _action_expire(self):
        pickings_to_cancel = self.env['stock.picking']
        rmas = self.filtered(lambda rma: rma.in_picking_state != 'done' and rma.out_picking_state != 'done')
        pickings_to_cancel += rmas.filtered(lambda r: r.in_picking_id).mapped('in_picking_id')
        pickings_to_cancel += rmas.filtered(lambda r: r.out_picking_id).mapped('out_picking_id')
        pickings_to_cancel.action_cancel()
        rmas.write({'state': 'expired'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('rma.rma') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.rma') or _('New')

        # Provide defaults on create (e.g. from portal)
        if vals.get('template_id'):
            template = self.env['rma.template'].browse(vals.get('template_id'))
            if 'initial_in_picking_carrier_id' not in vals:
                vals['initial_in_picking_carrier_id'] = template.in_carrier_id.id
            if 'initial_out_picking_carrier_id' not in vals:
                vals['initial_out_picking_carrier_id'] = template.out_carrier_id.id
            if template.valid_days and 'validity_date' not in vals:
                now = datetime.now()
                vals['validity_date'] = now + timedelta(days=template.valid_days)

        result = super(RMA, self).create(vals)
        result.template_id._schedule_responsible_activities(result)
        return result

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

    def action_done(self):
        for rma in self:
            if rma.in_picking_id and rma.in_picking_id.state not in ('done', 'cancel'):
                raise UserError(_('Inbound picking not complete or cancelled.'))
            if rma.out_picking_id and rma.out_picking_id.state not in ('done', 'cancel'):
                raise UserError(_('Outbound picking not complete or cancelled.'))
        self.write({'state': 'done'})

    def action_cancel(self):
        for rma in self:
            rma.in_picking_id.action_cancel()
            rma.out_picking_id.action_cancel()
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.filtered(lambda l: l.state in ('cancel', 'expired')).write({
            'state': 'draft', 'in_picking_id': False, 'out_picking_id': False})

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

    def action_in_picking_send_to_shipper(self):
        for rma in self:
            if rma.in_picking_id and rma.in_picking_carrier_id:
                rma.in_picking_id.send_to_shipper()

    def action_add_picking_lines(self):
        make_line_obj = self.env['rma.picking.make.lines']
        for rma in self:
            lines = make_line_obj.create({
                'rma_id': rma.id,
            })
            action = self.env.ref('rma.action_rma_add_lines').read()[0]
            action['res_id'] = lines.id
            return action

    def unlink(self):
        for rma in self:
            if rma.state not in ('draft'):
                raise UserError(_('You can not delete a non-draft RMA.'))
        return super(RMA, self).unlink()

    def _picking_from_values(self, values, values_update, move_line_values_update):
        values.update(values_update)
        move_lines = []
        for l1, l2, vals in values['move_lines']:
            vals.update(move_line_values_update)
            move_lines.append((l1, l2, vals))
        values['move_lines'] = move_lines
        return self.env['stock.picking'].sudo().create(values)

    def _new_in_picking(self, old_picking):
        new_picking = old_picking.copy({
            'move_lines': [],
            'picking_type_id': self.template_id.in_type_id.id,
            'state': 'draft',
            'origin': old_picking.name + ' ' + self.name,
            'location_id': self.template_id.in_location_id.id,
            'location_dest_id': self.template_id.in_location_dest_id.id,
            'carrier_id': self.initial_in_picking_carrier_id.id,
            'carrier_tracking_ref': False,
            'carrier_price': False
        })
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return new_picking

    def _new_in_move_vals(self, rma_line, new_picking, old_move):
        return {
                'name': self.name + ' IN: ' + rma_line.product_id.name_get()[0][1],
                'product_id': rma_line.product_id.id,
                'product_uom_qty': rma_line.product_uom_qty,
                'product_uom': rma_line.product_uom_id.id,
                'picking_id': new_picking.id,
                'state': 'draft',
                'location_id': old_move.location_dest_id.id,
                'location_dest_id': self.template_id.in_location_dest_id.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': new_picking.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': old_move.id,
                'procure_method': self.template_id.in_procure_method,
                'to_refund': self.template_id.in_to_refund,
            }

    def _new_in_moves(self, old_picking, new_picking, move_update):
        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1)
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))

        moves = self.env['stock.move']
        for l in lines:
            return_move = old_picking.move_lines.filtered(lambda ol: ol.state == 'done' and ol.product_id.id == l.product_id.id)[0]
            copy_vals = self._new_in_move_vals(l, new_picking, return_move)
            copy_vals.update(move_update)
            r = return_move.copy(copy_vals)
            vals = {}
            # +--------------------------------------------------------------------------------------------------------+
            # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
            # |              | returned_move_ids              ↑                                  | returned_move_ids
            # |              ↓                                | return_line.move_id              ↓
            # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
            # +--------------------------------------------------------------------------------------------------------+
            move_orig_to_link = return_move.move_dest_ids.mapped('returned_move_ids')
            move_dest_to_link = return_move.move_orig_ids.mapped('returned_move_ids')
            vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_move]
            vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
            r.write(vals)
            moves += r
        return moves

    def _new_out_picking(self, old_picking):
        new_picking = old_picking.copy({
            'move_lines': [],
            'picking_type_id': self.template_id.out_type_id.id,
            'state': 'draft',
            'origin': old_picking.name + ' ' + self.name,
            'location_id': self.template_id.out_location_id.id,
            'location_dest_id': self.template_id.out_location_dest_id.id,
            'carrier_id': self.initial_out_picking_carrier_id.id,
            'carrier_tracking_ref': False,
            'carrier_price': False
        })
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return new_picking

    def _new_out_move_vals(self, rma_line, new_picking, old_move):
        return {
                'name': self.name + ' OUT: ' + rma_line.product_id.name_get()[0][1],
                'product_id': rma_line.product_id.id,
                'product_uom_qty': rma_line.product_uom_qty,
                'picking_id': new_picking.id,
                'state': 'draft',
                'location_id': self.template_id.out_location_id.id,
                'location_dest_id': self.template_id.out_location_dest_id.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': new_picking.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': False,
                'procure_method': self.template_id.out_procure_method,
                'to_refund': self.template_id.out_to_refund,
            }

    def _new_out_moves(self, old_picking, new_picking, move_update):
        lines = self.lines.filtered(lambda l: l.product_uom_qty >= 1)
        if not lines:
            raise UserError(_('You have no lines with positive quantity.'))
        moves = self.env['stock.move']
        for l in lines:
            return_move = old_picking.move_lines.filtered(lambda ol: ol.state == 'done' and ol.product_id.id == l.product_id.id)[0]
            copy_vals = self._new_out_move_vals(l, new_picking, return_move)
            copy_vals.update(move_update)
            moves += return_move.copy(copy_vals)
        return moves

    def _create_in_picking_stock_picking(self):
        if not self.stock_picking_id or self.stock_picking_id.state != 'done':
            raise UserError(_('You must have a completed stock picking for this RMA.'))
        if not self.template_id.in_require_return:
            group_id = self.stock_picking_id.group_id.id if self.stock_picking_id.group_id else 0
            values = self.template_id._values_for_in_picking(self)
            update = {'group_id': group_id}
            return self._picking_from_values(values, update, update)

        old_picking = self.stock_picking_id

        new_picking = self._new_in_picking(old_picking)
        self._new_in_moves(old_picking, new_picking, {})
        return new_picking

    def _create_out_picking_stock_picking(self):
        if not self.stock_picking_id or self.stock_picking_id.state != 'done':
            raise UserError(_('You must have a completed stock picking for this RMA.'))
        if not self.template_id.out_require_return:
            group_id = self.stock_picking_id.group_id.id if self.stock_picking_id.group_id else 0
            values = self.template_id._values_for_out_picking(self)
            update = {'group_id': group_id}
            return self._picking_from_values(values, update, update)

        old_picking = self.stock_picking_id
        new_picking = self._new_out_picking(old_picking)
        self._new_out_moves(old_picking, new_picking, {})
        return new_picking


class RMALine(models.Model):
    _name = 'rma.line'
    _description = 'RMA Line'

    rma_id = fields.Many2one('rma.rma', string='RMA')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('uom.uom', 'UOM')
    product_uom_qty = fields.Float(string='QTY')
    rma_template_usage = fields.Selection(related='rma_id.template_usage')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id
