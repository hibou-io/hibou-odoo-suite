from odoo.tools.float_utils import float_round, float_is_zero
from odoo.addons.delivery_easypost.models.easypost_request import EasypostRequest

# Patches to add customs lines during SO rating.

def _prepare_order_shipments(self, carrier, order):
    """ Method used in order to estimate delivery
    cost for a quotation. It estimates the price with
    the default package defined on the carrier.
    e.g: if the default package on carrier is a 10kg Fedex
    box and the customer ships 35kg it will create a shipment
    with 4 packages (3 with 10kg and the last with 5 kg.).
    It ignores reality with dimension or the fact that items
    can not be cut in multiple pieces in order to allocate them
    in different packages. It also ignores customs info.
    """
    # Max weight for carrier default package
    max_weight = carrier._easypost_convert_weight(carrier.easypost_default_packaging_id.max_weight)
    # Order weight
    total_weight = carrier._easypost_convert_weight(
        sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line if not line.display_type]))

    # Create shipments
    shipments = {}
    if max_weight and total_weight > max_weight:
        # Integer division for packages with maximal weight.
        total_shipment = int(total_weight // max_weight)
        # Remainder for last package.
        last_shipment_weight = float_round(total_weight % max_weight, precision_digits=1)
        for shp_id in range(0, total_shipment):
            shipments.update(self._prepare_parcel(shp_id, carrier.easypost_default_packaging_id, max_weight,
                                                  carrier.easypost_label_file_type))
            shipments.update(self._customs_info_sale_order(shp_id, order.order_line))
            shipments.update(self._options(shp_id, carrier))
        if not float_is_zero(last_shipment_weight, precision_digits=1):
            shipments.update(
                self._prepare_parcel(total_shipment, carrier.easypost_default_packaging_id, last_shipment_weight,
                                     carrier.easypost_label_file_type))
            shipments.update(self._customs_info_sale_order(shp_id, order.order_line))
            shipments.update(self._options(total_shipment, carrier))
    else:
        shipments.update(self._prepare_parcel(0, carrier.easypost_default_packaging_id, total_weight,
                                              carrier.easypost_label_file_type))
        shipments.update(self._customs_info_sale_order(0, order.order_line))
        shipments.update(self._options(0, carrier))
    return shipments

def _customs_info_sale_order(self, shipment_id, lines):
    """ generate a dict with customs info for each package... or each line
    https://www.easypost.com/customs-guide.html
    Currently general customs info for all packages are not generate.
    For each shipment add a customs items by move line containing
    - Product description (care it crash if bracket are used)
    - Quantity for this product in the current package
    - Product price
    - Product price currency
    - Total weight in ounces.
    - Original country code(warehouse)
    """
    customs_info = {}
    customs_item_id = 0
    for line in lines:
        # skip service
        if line.product_id.type not in ['product', 'consu']:
            continue
        unit_quantity = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id,
                                                           rounding_method='HALF-UP')
        hs_code = line.product_id.hs_code or ''
        price_unit = line.price_reduce_taxinc
        customs_info.update({
            'order[shipments][%d][customs_info][customs_items][%d][description]' % (
            shipment_id, customs_item_id): line.product_id.name,
            'order[shipments][%d][customs_info][customs_items][%d][quantity]' % (
            shipment_id, customs_item_id): unit_quantity,
            'order[shipments][%d][customs_info][customs_items][%d][value]' % (
            shipment_id, customs_item_id): unit_quantity * price_unit,
            'order[shipments][%d][customs_info][customs_items][%d][currency]' % (
            shipment_id, customs_item_id): line.order_id.company_id.currency_id.name,
            'order[shipments][%d][customs_info][customs_items][%d][weight]' % (shipment_id, customs_item_id):
                line.env['delivery.carrier']._easypost_convert_weight(line.product_id.weight * unit_quantity),
            'order[shipments][%d][customs_info][customs_items][%d][origin_country]' % (
            shipment_id, customs_item_id): line.order_id.warehouse_id.partner_id.country_id.code,
            'order[shipments][%d][customs_info][customs_items][%d][hs_tariff_number]' % (
            shipment_id, customs_item_id): hs_code,
        })
        customs_item_id += 1
    return customs_info

# Patch to prevent sending delivery customs for same-country-shipments
def _customs_info(self, shipment_id, lines):
    """ generate a dict with customs info for each package.
    https://www.easypost.com/customs-guide.html
    Currently general customs info for all packages are not generate.
    For each shipment add a customs items by move line containing
    - Product description (care it crash if bracket are used)
    - Quantity for this product in the current package
    - Product price
    - Product price currency
    - Total weight in ounces.
    - Original country code(warehouse)
    """
    customs_info = {}
    customs_item_id = 0
    for line in lines:
        # Customization to return early if same country
        # only need early return if one line does this
        if line.picking_id.picking_type_id.warehouse_id.partner_id.country_id.code == line.picking_id.partner_id.country_id.code:
            return {}

        # skip service
        if line.product_id.type not in ['product', 'consu']:
            continue
        if line.picking_id.picking_type_code == 'incoming':
            unit_quantity = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id, rounding_method='HALF-UP')
        else:
            unit_quantity = line.product_uom_id._compute_quantity(line.qty_done, line.product_id.uom_id, rounding_method='HALF-UP')
        hs_code = line.product_id.hs_code or ''
        price_unit = line.move_id.sale_line_id.price_reduce_taxinc if line.move_id.sale_line_id else line.product_id.list_price
        customs_info.update({
            'order[shipments][%d][customs_info][customs_items][%d][description]' % (shipment_id, customs_item_id): line.product_id.name,
            'order[shipments][%d][customs_info][customs_items][%d][quantity]' % (shipment_id, customs_item_id): unit_quantity,
            'order[shipments][%d][customs_info][customs_items][%d][value]' % (shipment_id, customs_item_id): unit_quantity * price_unit,
            'order[shipments][%d][customs_info][customs_items][%d][currency]' % (shipment_id, customs_item_id): line.picking_id.company_id.currency_id.name,
            'order[shipments][%d][customs_info][customs_items][%d][weight]' % (shipment_id, customs_item_id): line.env['delivery.carrier']._easypost_convert_weight(line.product_id.weight * unit_quantity),
            'order[shipments][%d][customs_info][customs_items][%d][origin_country]' % (shipment_id, customs_item_id): line.picking_id.picking_type_id.warehouse_id.partner_id.country_id.code,
            'order[shipments][%d][customs_info][customs_items][%d][hs_tariff_number]' % (shipment_id, customs_item_id): hs_code,
        })
        customs_item_id += 1
    return customs_info

EasypostRequest._prepare_order_shipments = _prepare_order_shipments
EasypostRequest._customs_info_sale_order = _customs_info_sale_order
EasypostRequest._customs_info = _customs_info
