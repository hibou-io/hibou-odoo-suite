from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    automatic_insurance_value = fields.Float(string='Automatic Insurance Value',
                                             help='Will be used during shipping to determine if the '
                                                  'picking\'s value warrants insurance being added.')
    automatic_sig_req_value = fields.Float(string='Automatic Signature Required Value',
                                           help='Will be used during shipping to determine if the '
                                                'picking\'s value warrants signature required being added.')
    procurement_priority = fields.Selection(PROCUREMENT_PRIORITIES,
                                            string='Procurement Priority',
                                            help='Priority for this carrier. Will affect pickings '
                                                 'and procurements related to this carrier.')
    package_by_field = fields.Selection([
        ('', 'Use Default Package Type'),
        ('weight', 'Weight'),
        ('volume', 'Volume'),
    ], string='Packaging by Product Field')

    # Package selection
    def get_package_type_for_order(self, order):
        if self.package_by_field == 'weight':
            return self._get_package_type_for_order(order, 'max_weight', 'weight')
        elif self.package_by_field == 'volume':
            return self._get_package_type_for_order(order, 'package_volume', 'volume')
        attr = getattr(self, '%s_default_packaging_id' % (self.delivery_type, ), None)
        if attr:
            return attr()
        attr = getattr(self, '%s_default_package_type_id' % (self.delivery_type, ), None)
        if attr:
            return attr()
        return self.env['stock.package.type']

    def _get_package_type_for_order(self, order, package_type_field, product_field):
        order_total = sum(order.order_line.filtered(lambda ol: ol.product_id.type in ('product', 'consu')).mapped(lambda ol: ol.product_id[product_field] * ol.product_uom_qty))
        if order_total:
            package_types = self.env['stock.package.type'].search([
                ('package_carrier_type', 'in', ('none', False, self.delivery_type)),
                ('use_in_package_selection', '=', True),
            ], order=package_type_field)
            package_type = None
            for package_type in package_types:
                if package_type[package_type_field] >= order_total:
                    return package_type
            return package_types if not package_type else package_type

    # Utility
    def get_to_ship_picking_packages(self, picking):
        # Will return a stock.quant.package record set if the picking has packages
        # in the case of multi-packing and none applicable, will return None
        # Additionally, will not return packages that have a tracking number (because they have shipped)
        picking_packages = picking.package_ids
        package_carriers = picking_packages.mapped('carrier_id')
        if package_carriers:
            # only ship ours
            picking_packages = picking_packages.filtered(lambda p: p.carrier_id == self and not p.carrier_tracking_ref)

            if package_carriers and not picking_packages:
                return None
        return picking_packages
    
    def get_insurance_value(self, order=None, picking=None, package=None):
        value = 0.0
        if order:
            if order.order_line:
                value = sum(order.order_line.filtered(lambda l: l.product_id.type != 'service').mapped('price_subtotal'))
            else:
                return value
        if picking:
            value = picking.declared_value(package=package)
            if package and not package.require_insurance:
                value = 0.0
            else:
                if picking.require_insurance == 'no':
                    value = 0.0
                elif picking.require_insurance == 'auto' and self.automatic_insurance_value and self.automatic_insurance_value > value:
                    value = 0.0
        return value

    def get_signature_required(self, order=None, picking=None, package=None):
        value = 0.0
        if order:
            if order.order_line:
                value = sum(order.order_line.filtered(lambda l: l.product_id.type != 'service').mapped('price_subtotal'))
            else:
                return False
        if picking:
            value = picking.declared_value(package=package)
            if package:
                return package.require_signature
            else:
                if picking.require_signature == 'no':
                    return False
                elif picking.require_signature == 'yes':
                    return True
        return self.automatic_sig_req_value and value >= self.automatic_sig_req_value

    def get_third_party_account(self, order=None, picking=None):
        if order and order.shipping_account_id:
            return order.shipping_account_id
        if picking and picking.shipping_account_id:
            return picking.shipping_account_id
        return None

    def get_order_name(self, order=None, picking=None):
        if order:
            return order.name
        if picking:
            if picking.sale_id:
                return picking.sale_id.name  # + ' - ' + picking.name
            return picking.name
        return ''

    def get_attn(self, order=None, picking=None):
        if order:
            return order.client_order_ref
        if picking and picking.sale_id:
            return picking.sale_id.client_order_ref
        # If Picking has a reference, decide what it is.
        return False

    def _classify_picking(self, picking):
        if picking.picking_type_id.code == 'incoming' and picking.location_id.usage == 'supplier' and picking.location_dest_id.usage == 'customer':
            return 'dropship'
        elif picking.picking_type_id.code == 'incoming' and picking.location_id.usage == 'customer' and picking.location_dest_id.usage == 'supplier':
            return 'dropship_in'
        elif picking.picking_type_id.code == 'incoming':
            return 'in'
        return 'out'

    def is_amazon(self, order=None, picking=None):
        """
        Amazon MWS orders potentially need to be flagged for
        clean up on the carrier's side.

        Override to return based on criteria in your company.
        :return:
        """
        return False

    # Shipper Company

    def get_shipper_company(self, order=None, picking=None):
        """
        Shipper Company: The `res.partner` that provides the name of where the shipment is coming from.
        """
        if order:
            return order.company_id.partner_id
        if picking:
            return getattr(self, ('_get_shipper_company_%s' % (self._classify_picking(picking),)),
                           self._get_shipper_company_out)(picking)
        return None

    def _get_shipper_company_dropship(self, picking):
        return picking.company_id.partner_id

    def _get_shipper_company_dropship_in(self, picking):
        return picking.company_id.partner_id

    def _get_shipper_company_in(self, picking):
        return picking.company_id.partner_id

    def _get_shipper_company_out(self, picking):
        return picking.company_id.partner_id

    # Shipper Warehouse

    def get_shipper_warehouse(self, order=None, picking=None):
        """
        Shipper Warehouse: The `res.partner` that is basically the physical address a shipment is coming from.
        """
        if order:
            return order.warehouse_id.partner_id
        if picking:
            return getattr(self, ('_get_shipper_warehouse_%s' % (self._classify_picking(picking),)),
                           self._get_shipper_warehouse_out)(picking)
        return None

    def _get_shipper_warehouse_dropship(self, picking):
        return picking.partner_id

    def _get_shipper_warehouse_dropship_in(self, picking):
        if picking.sale_id:
            picking.sale_id.partner_shipping_id
        return self._get_shipper_warehouse_dropship_in_no_sale(picking)

    def _get_shipper_warehouse_dropship_in_no_sale(self, picking):
        return picking.company_id.partner_id

    def _get_shipper_warehouse_in(self, picking):
        return picking.partner_id

    def _get_shipper_warehouse_out(self, picking):
        return picking.picking_type_id.warehouse_id.partner_id

    # Recipient

    def get_recipient(self, order=None, picking=None):
        """
        Recipient: The `res.partner` receiving the shipment.
        """
        if order:
            return order.partner_shipping_id
        if picking:
            return getattr(self, ('_get_recipient_%s' % (self._classify_picking(picking),)),
                           self._get_recipient_out)(picking)
        return None

    def _get_recipient_dropship(self, picking):
        if picking.sale_id:
            return picking.sale_id.partner_shipping_id
        return picking.partner_id

    def _get_recipient_dropship_no_sale(self, picking):
        return picking.company_id.partner_id

    def _get_recipient_dropship_in(self, picking):
        return picking.picking_type_id.warehouse_id.partner_id

    def _get_recipient_in(self, picking):
        return picking.picking_type_id.warehouse_id.partner_id

    def _get_recipient_out(self, picking):
        return picking.partner_id

    # -------------------------- #
    # API for external providers #
    # -------------------------- #
    def rate_shipment_multi(self, order=None, picking=None, packages=None):
        ''' Compute the price of the order shipment

        :param order: record of sale.order or None
        :param picking: record of stock.picking or None
        :param packages: recordset of stock.quant.package or None (requires picking also set)
        :return list: dict: {
                       'carrier': delivery.carrier(),
                       'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message,
                       'date_planned': a datetime for when the shipment is supposed to leave,
                       'date_delivered': a datetime for when the shipment is supposed to arrive,
                       'transit_days': a Float for how many days it takes in transit,
                       'service_code': a string that represents the service level/agreement,
                       'package': stock.quant.package(),
                       }

        e.g. self == delivery.carrier(5, 6)
        then return might be:
        [
            {'carrier': delivery.carrier(5), 'price': 10.50, 'service_code': 'GROUND_HOME_DELIVERY', ...},
            {'carrier': delivery.carrier(7), 'price': 12.99, 'service_code': 'FEDEX_EXPRESS_SAVER', ...},  # NEW!
            {'carrier': delivery.carrier(6), 'price': 8.0, 'service_code': 'USPS_PRI', ...},
        ]
        '''
        self.ensure_one()

        if picking:
            self = self.with_context(date_planned=fields.Datetime.now())
            if not packages:
                packages = picking.package_ids
        else:
            if packages:
                raise UserError(_('Cannot rate package without picking.'))
            self = self.with_context(date_planned=('date_planned' in order._fields and order.date_planned or fields.Datetime.now()))

        res = []
        for carrier in self:
            carrier_packages = packages and packages.filtered(lambda p: not p.carrier_tracking_ref and
                                                              (not p.carrier_id or p.carrier_id == carrier) and
                                                              p.package_type_id.package_carrier_type in (False, '', 'none', carrier.delivery_type))
            if packages and not carrier_packages:
                continue
            if hasattr(carrier, '%s_rate_shipment_multi' % self.delivery_type):
                try:
                    res += getattr(carrier, '%s_rate_shipment_multi' % carrier.delivery_type)(order=order,
                                                                                                   picking=picking,
                                                                                                   packages=carrier_packages)
                except TypeError:
                    # TODO remove catch if after Odoo 14
                    # This is intended to find ones that don't support packages= kwarg
                    res += getattr(carrier, '%s_rate_shipment_multi' % carrier.delivery_type)(order=order,
                                                                                                   picking=picking)

        return res

    def cancel_shipment(self, pickings, packages=None):
        ''' Cancel a shipment

        :param pickings: A recordset of pickings
        :param packages: Optional recordset of packages (should be for this carrier)
        '''
        self.ensure_one()
        if hasattr(self, '%s_cancel_shipment' % self.delivery_type):
            # No good way to tell if this method takes the kwarg for packages
            if packages:
                try:
                    return getattr(self, '%s_cancel_shipment' % self.delivery_type)(pickings, packages=packages)
                except TypeError:
                    # we won't be able to cancel the packages properly
                    # here we will TRY to make a good call here where we put the package references into the picking
                    # and let the original mechanisms try to work here
                    tracking_ref = ','.join(packages.mapped('carrier_tracking_ref'))
                    pickings.write({
                        'carrier_id': self.id,
                        'carrier_tracking_ref': tracking_ref,
                    })

            return getattr(self, '%s_cancel_shipment' % self.delivery_type)(pickings)


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'

    package_declared_value = fields.Float(string='Declared Value')
    package_require_insurance = fields.Boolean(string='Require Insurance')
    package_require_signature = fields.Boolean(string='Require Signature')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'package_declared_value' in fields_list:
            picking = self.env['stock.picking'].browse(defaults.get('picking_id'))
            move_line_ids = picking.move_line_ids.filtered(lambda m:
                float_compare(m.qty_done, 0.0, precision_rounding=m.product_uom_id.rounding) > 0
                and not m.result_package_id
            )
            total_value = 0.0
            for ml in move_line_ids:
                qty = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                total_value += qty * ml.product_id.standard_price
            defaults['package_declared_value'] = total_value
        return defaults

    @api.onchange('package_declared_value')
    def _onchange_package_declared_value(self):
        picking = self.picking_id
        value = self.package_declared_value
        if picking.require_insurance == 'auto':
            self.package_require_insurance = value and picking.carrier_id.automatic_insurance_value and value >= picking.carrier_id.automatic_insurance_value
        else:
            self.package_require_insurance = picking.require_insurance == 'yes'
        if picking.require_signature == 'auto':
            self.package_require_signature = value and picking.carrier_id.automatic_sig_req_value and value >= picking.carrier_id.automatic_sig_req_value
        else:
            self.package_require_signature = picking.require_signature == 'yes'

    def action_put_in_pack(self):
        # Copied because `delivery_package` is not retained by reference or returned...
        picking_move_lines = self.picking_id.move_line_ids
        if not self.picking_id.picking_type_id.show_reserved and not self.env.context.get('barcode_view'):
            picking_move_lines = self.picking_id.move_line_nosuggest_ids

        move_line_ids = picking_move_lines.filtered(lambda ml:
                                                    float_compare(ml.qty_done, 0.0,
                                                                  precision_rounding=ml.product_uom_id.rounding) > 0
                                                    and not ml.result_package_id
                                                    )
        if not move_line_ids:
            move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                                                                 precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(
                ml.qty_done, 0.0,
                precision_rounding=ml.product_uom_id.rounding) == 0)

        delivery_package = self.picking_id._put_in_pack(move_line_ids)
        # write shipping weight and package type on 'stock_quant_package' if needed
        if self.delivery_package_type_id:
            delivery_package.package_type_id = self.delivery_package_type_id
        if self.shipping_weight:
            delivery_package.shipping_weight = self.shipping_weight
        # Hibou : Fill additional fields.
        delivery_package.write({
            'declared_value': self.package_declared_value,
            'require_insurance': self.package_require_insurance,
            'require_signature': self.package_require_signature,
        })
