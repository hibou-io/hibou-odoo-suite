# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    def _get_ups_signature_required_type(self, order=None, picking=None, package=None):
        # '3' for Adult Sig.
        return '2'

    def _get_ups_signature_required(self, order=None, picking=None, package=None):
        if self.get_signature_required(order=order, picking=picking, package=package):
            return self._get_ups_signature_required_type(order=order, picking=picking, package=package)
        return False
    
    def _get_main_ups_account_number(self, order=None, picking=None):
        wh = None
        if order:
            wh = order.warehouse_id
        if picking:
            wh = picking.picking_type_id.warehouse_id
        if wh and wh.ups_shipper_number:
            return wh.ups_shipper_number
        return self.ups_shipper_number
    
    def _get_ups_account_number(self, order=None, picking=None):
        """
        Common hook to customize what UPS Account number to use.
        :return: UPS Account Number
        """
        # Provided by Hibou Odoo Suite `delivery_hibou`
        third_party_account = self.get_third_party_account(order=order, picking=picking)
        if third_party_account:
            if not third_party_account.delivery_type == 'ups':
                raise ValidationError('Non-UPS Shipping Account indicated during UPS shipment.')
            return third_party_account.name
        if picking and picking.picking_type_id.warehouse_id.ups_shipper_number:
            return picking.picking_type_id.warehouse_id.ups_shipper_number
        return self.ups_shipper_number
    
    def _get_ups_carrier_account(self, picking):
        # 3rd party billing should return False if not used.
        account = self._get_ups_account_number(picking=picking)
        return account if account not in (self.ups_shipper_number, picking.picking_type_id.warehouse_id.ups_shipper_number) else False
