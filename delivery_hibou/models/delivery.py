from odoo import fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    automatic_insurance_value = fields.Float(string='Automatic Insurance Value',
                                             help='Will be used during shipping to determine if the '
                                                  'picking\'s value warrants insurance being added.')
    procurement_priority = fields.Selection(PROCUREMENT_PRIORITIES,
                                            string='Procurement Priority',
                                            help='Priority for this carrier. Will affect pickings '
                                                 'and procurements related to this carrier.')

    # Utility

    def get_insurance_value(self, order=None, picking=None):
        value = 0.0
        if order:
            if order.order_line:
                value = sum(order.order_line.filtered(lambda l: l.type != 'service').mapped('price_subtotal'))
            else:
                return value
        if picking:
            value = picking.declared_value()
            if picking.require_insurance == 'no':
                value = 0.0
            elif picking.require_insurance == 'auto' and self.automatic_insurance_value and self.automatic_insurance_value > value:
                value = 0.0
        return value

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
