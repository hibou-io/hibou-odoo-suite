from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'
    
    use_in_package_selection = fields.Boolean()
    package_volume = fields.Float(compute='_compute_package_volume', store=True)
    
    @api.depends('packaging_length', 'width', 'height')
    def _compute_package_volume(self):
        for pt in self:
            pt.package_volume = pt.packaging_length * pt.width * pt.height


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one('delivery.carrier', string='Carrier')
    carrier_tracking_ref = fields.Char(string='Tracking Reference')
    require_insurance = fields.Boolean(string='Require Insurance')
    require_signature = fields.Boolean(string='Require Signature')
    declared_value = fields.Float(string='Declared Value')

    def _get_active_picking(self):
        picking_id = self._context.get('active_id')
        picking_model = self._context.get('active_model')
        if not picking_id or picking_model != 'stock.picking':
            raise UserError(_('Cannot cancel package other than through shipment/picking.'))
        return self.env['stock.picking'].browse(picking_id)

    def send_to_shipper(self):
        picking = self._get_active_picking()
        picking.with_context(packages=self).send_to_shipper()

    def cancel_shipment(self):
        picking = self._get_active_picking()
        picking.with_context(packages=self).cancel_shipment()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipping_account_id = fields.Many2one('partner.shipping.account', string='Shipping Account')
    require_insurance = fields.Selection([
            ('auto', 'Automatic'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Require Insurance', default='auto',
        help='If your carrier supports it, auto should be calculated off of the "Automatic Insurance Value" field.')
    require_signature = fields.Selection([
            ('auto', 'Automatic'),
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Require Signature', default='auto',
        help='If your carrier supports it, auto should be calculated off of the "Automatic Signature Required Value" field.')
    package_carrier_tracking_ref = fields.Char(string='Package Tracking Numbers', compute='_compute_package_carrier_tracking_ref')
    commercial_partner_id = fields.Many2one('res.partner', related='partner_id.commercial_partner_id')

    @api.depends('move_line_ids.package_id.carrier_tracking_ref')
    def _compute_package_carrier_tracking_ref(self):
        for picking in self:
            package_refs = picking.package_ids.filtered('carrier_tracking_ref').mapped('carrier_tracking_ref')
            if package_refs:
                picking.package_carrier_tracking_ref = ','.join(package_refs)
            else:
                picking.package_carrier_tracking_ref = False

    @api.onchange('carrier_id')
    def _onchange_carrier_id_for_priority(self):
        for picking in self:
            if picking.carrier_id and picking.carrier_id.procurement_priority:
                picking.priority = picking.carrier_id.procurement_priority

    @api.model
    def create(self, values):
        origin = values.get('origin')
        if origin and not values.get('shipping_account_id'):
            so = self.env['sale.order'].search([('name', '=', str(origin))], limit=1)
            if so and so.shipping_account_id:
                values['shipping_account_id'] = so.shipping_account_id.id
        carrier_id = values.get('carrier_id')
        if carrier_id:
            carrier = self.env['delivery.carrier'].browse(carrier_id)
            if carrier.procurement_priority:
                values['priority'] = carrier.procurement_priority

        res = super(StockPicking, self).create(values)
        return res

    def declared_value(self, package=None):
        self.ensure_one()
        if package:
            return package.declared_value
        cost = sum([(l.product_id.standard_price * l.qty_done) for l in self.move_line_ids] or [0.0])
        if not cost:
            # Assume Full Value
            cost = sum([(l.product_id.standard_price * l.product_uom_qty) for l in self.move_lines] or [0.0])
        return cost

    def clear_carrier_tracking_ref(self):
        self.write({'carrier_tracking_ref': False})

    def reset_carrier_tracking_ref(self):
        for picking in self:
            picking.carrier_tracking_ref = picking.package_carrier_tracking_ref

    # Override to send to specific packaging carriers
    def send_to_shipper(self):
        packages = self._context.get('packages')
        self.ensure_one()
        if not packages:
            packages = self.package_ids
        package_carriers = packages.mapped('carrier_id')
        if not package_carriers:
            # Original behavior
            return super().send_to_shipper()

        tracking_numbers = []
        carrier_prices = []
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        for carrier in package_carriers:
            self.carrier_id = carrier
            carrier_packages = packages.filtered(lambda p: p.carrier_id == carrier)
            res = carrier.send_shipping(self)
            if res:
                res = res[0]
                if carrier.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= carrier.amount:
                    res['exact_price'] = 0.0
                carrier_price = res['exact_price'] * (1.0 + (self.carrier_id.margin / 100.0))
                carrier_prices.append(carrier_price)
                tracking_number = ''
                if res['tracking_number']:
                    tracking_number = res['tracking_number']
                    tracking_numbers.append(tracking_number)
                    # Try to add tracking to the individual packages.
                    potential_tracking_numbers = tracking_number.split(',')
                    if len(potential_tracking_numbers) == 1:
                        potential_tracking_numbers = tracking_number.split('+')  # UPS for example...
                    if len(potential_tracking_numbers) >= len(carrier_packages):
                        for t, p in zip(potential_tracking_numbers, carrier_packages):
                            p.carrier_tracking_ref = t
                    else:
                        carrier_packages.write({'carrier_tracking_ref': tracking_number})
                msg = _(
                    "Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
                    carrier_name=carrier.name,
                    ref=tracking_number,
                    price=carrier_price,
                    currency=order_currency.name
                )
                self.message_post(body=msg)

        self.carrier_price = sum(carrier_prices or [0.0])
        self.carrier_tracking_ref = ','.join(tracking_numbers or [''])
        self._add_delivery_cost_to_so()

    # Override to provide per-package versions...
    def cancel_shipment(self):
        packages = self._context.get('packages')
        pickings_with_package_tracking = self.filtered(lambda p: p.package_carrier_tracking_ref)
        for picking in pickings_with_package_tracking:
            if packages:
                current_packages = packages
            else:
                current_packages = picking.package_ids
            # Packages without a carrier can just be cleared
            packages_without_carrier = current_packages.filtered(lambda p: not p.carrier_id and p.carrier_tracking_ref)
            packages_without_carrier.write({
                'carrier_tracking_ref': False,
            })
            # Packages with carrier can use the carrier method
            packages_with_carrier = current_packages.filtered(lambda p: p.carrier_id and p.carrier_tracking_ref)
            carriers = packages_with_carrier.mapped('carrier_id')
            for carrier in carriers:
                carrier_packages = packages_with_carrier.filtered(lambda p: p.carrier_id == carrier)
                carrier.cancel_shipment(self, packages=carrier_packages)
                # Above cancel should also say which are cancelled in chatter.
                # package_refs = ','.join(carrier_packages.mapped('carrier_tracking_ref'))
                # msg = "Shipment %s cancelled" % package_refs
                # picking.message_post(body=msg)
                carrier_packages.write({'carrier_tracking_ref': False})

        pickings_without_package_tracking = self - pickings_with_package_tracking
        if pickings_without_package_tracking:
            # use original on these
            super(StockPicking, pickings_without_package_tracking).cancel_shipment()
