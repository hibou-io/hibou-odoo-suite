from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    maintenance_request_id = fields.Many2one('maintenance.request')


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    repair_location_id = fields.Many2one('stock.location', string='Default Repair Parts Source')
    repair_location_dest_id = fields.Many2one('stock.location', string='Default Repair Parts Destination')


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_type = fields.Selection(selection_add=[('negligence', 'Negligence')])
    repair_line_ids = fields.One2many('maintenance.request.repair.line', 'request_id', 'Parts', copy=True)
    repair_status = fields.Selection([
        ('repaired', 'Repaired'),
        ('to repair', 'To Repair'),
        ('no', 'Nothing to Repair')
        ], string='Repair Status', compute='_get_repaired', store=True, readonly=True)
    repair_location_id = fields.Many2one('stock.location', string='Source Location')
    repair_location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    total_lst_price = fields.Float(string='Total Price', compute='_compute_repair_totals', store=True)
    total_standard_price = fields.Float(string='Total Est. Cost', compute='_compute_repair_totals', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_repair_totals', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for request in res:
            request.repair_location_id = request.repair_location_id or request.maintenance_team_id.repair_location_id
            request.repair_location_dest_id = request.repair_location_id or request.maintenance_team_id.repair_location_dest_id
        return res

    @api.depends('repair_line_ids.lst_price', 'repair_line_ids.standard_price', 'repair_line_ids.cost')
    def _compute_repair_totals(self):
        for repair in self:
            repair.total_lst_price = sum(l.lst_price for l in repair.repair_line_ids)
            repair.total_standard_price = sum(l.standard_price for l in repair.repair_line_ids)
            repair.total_cost = sum(l.cost for l in repair.repair_line_ids)

    @api.depends('repair_line_ids.state')
    def _get_repaired(self):
        for request in self:
            if not request.repair_line_ids:
                request.repair_status = 'no'
            elif request.repair_line_ids.filtered(lambda l: l.state != 'done'):
                request.repair_status = 'to repair'
            else:
                request.repair_status = 'repaired'

    @api.onchange('maintenance_team_id')
    def _onchange_maintenance_team(self):
        for request in self:
            if request.maintenance_team_id:
                request.repair_location_id = request.maintenance_team_id.repair_location_id
                request.repair_location_dest_id = request.maintenance_team_id.repair_location_dest_id


    def action_complete_repair(self):
        for request in self.filtered(lambda r: r.repair_status == 'to repair'):
            request.repair_line_ids.action_complete()
        return True

class MaintenanceRequestRepairLine(models.Model):
    _name = 'maintenance.request.repair.line'
    _description = 'Maintenance Request Repair Lines'

    request_id = fields.Many2one('maintenance.request', copy=False)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity', default=1.0, digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='State', copy=False, default='draft')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    lst_price = fields.Float(string='Sale Price')
    standard_price = fields.Float(string='Est. Cost')
    cost = fields.Float(string='Cost', compute='_compute_actual_cost', store=True)
    
    def unlink(self):
        if self.filtered(lambda l: l.state == 'done'):
            raise UserError(_('Only draft lines can be deleted.'))
        return super(MaintenanceRequestRepairLine, self).unlink()

    @api.onchange('product_id', 'product_uom_qty')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.lst_price = self.product_id.lst_price * self.product_uom_qty
            self.standard_price = self.product_id.standard_price * self.product_uom_qty

    @api.depends('product_id', 'move_id')
    def _compute_actual_cost(self):
        for line in self:
            if line.move_id:
                line.cost = sum(abs(m.amount) for m in line.move_id.account_move_ids)
            else:
                line.cost = 0.0

    def _repair_complete_stock_move_values(self):
        values = {
            'name': self.request_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom_id.id,
            'location_id': self.request_id.repair_location_id.id,
            'location_dest_id': self.request_id.repair_location_dest_id.id,
            'maintenance_request_id': self.request_id.id,
            'origin': self.request_id.name,
        }
        # Optional modules for linking maintenance requests to projects, and stock moves to analytic accounts
        if hasattr(self.request_id, 'project_id') and hasattr(self.env['stock.move'], 'analytic_account_id'):
            values['analytic_account_id'] = self.request_id.project_id.analytic_account_id.id
        return values

    def action_complete(self):
        # Create stock movements. - Inspired by mrp_repair
        stock_move_model = self.env['stock.move']
        for line in self.filtered(lambda l: not l.state == 'done'):
            move = stock_move_model.create(self._repair_complete_stock_move_values())
            move = move.sudo()
            move._action_confirm()
            move._action_assign()
            if move.state != 'assigned':
                raise ValidationError(_('Unable to reserve inventory.'))

            move.quantity = line.product_uom_qty
            move.picked = True
            move._action_done()
            if move.state != 'done':
                raise ValidationError(_('Unable to move inventory.'))

            line.write({'move_id': move.id, 'state': 'done'})
        return True
