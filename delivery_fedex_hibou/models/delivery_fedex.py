# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import logging
import pytz
from odoo import fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.delivery_fedex.models.delivery_fedex import _convert_curr_iso_fdx
from .fedex_request import FedexRequest

pdf = tools.pdf
_logger = logging.getLogger(__name__)


class DeliveryFedex(models.Model):
    _inherit = 'delivery.carrier'

    fedex_service_type = fields.Selection(selection_add=[
        ('GROUND_HOME_DELIVERY', 'GROUND_HOME_DELIVERY'),
        ('FEDEX_EXPRESS_SAVER', 'FEDEX_EXPRESS_SAVER'),
    ])

    def _get_fedex_is_third_party(self, order=None, picking=None):
        third_party_account = self.get_third_party_account(order=order, picking=picking)
        if third_party_account:
            if not third_party_account.delivery_type == 'fedex':
                raise ValidationError('Non-FedEx Shipping Account indicated during FedEx shipment.')
            return True
        return False

    def _get_fedex_payment_account_number(self, order=None, picking=None):
        """
        Common hook to customize what Fedex Account number to use.
        :return: FedEx Account Number
        """
        # Provided by Hibou Odoo Suite `delivery_hibou`
        third_party_account = self.get_third_party_account(order=order, picking=picking)
        if third_party_account:
            if not third_party_account.delivery_type == 'fedex':
                raise ValidationError('Non-FedEx Shipping Account indicated during FedEx shipment.')
            return third_party_account.name
        if picking and picking.picking_type_id.warehouse_id.fedex_account_number:
            return picking.picking_type_id.warehouse_id.fedex_account_number
        return self.fedex_account_number

    def _get_fedex_account_number(self, order=None, picking=None):
        if order:
            # third_party_account = self.get_third_party_account(order=order, picking=picking)
            # if third_party_account:
            #     if not third_party_account.delivery_type == 'fedex':
            #         raise ValidationError('Non-FedEx Shipping Account indicated during FedEx shipment.')
            #     return third_party_account.name
            if order.warehouse_id.fedex_account_number:
                return order.warehouse_id.fedex_account_number
            return self.fedex_account_number
        if picking:
            if picking.picking_type_id.warehouse_id.fedex_account_number:
                return picking.picking_type_id.warehouse_id.fedex_account_number
        return self.fedex_account_number

    def _get_fedex_meter_number(self, order=None, picking=None):
        if order:
            if order.warehouse_id.fedex_meter_number:
                return order.warehouse_id.fedex_meter_number
            return self.fedex_meter_number
        if picking:
            if picking.picking_type_id.warehouse_id.fedex_meter_number:
                return picking.picking_type_id.warehouse_id.fedex_meter_number
        return self.fedex_meter_number

    def _get_fedex_recipient_is_residential(self, partner):
        if self.fedex_service_type.find('HOME') >= 0:
            return True
        return not (partner.is_company or partner.parent_id.is_company)

    """
    Overrides to use Hibou Delivery methods to get shipper etc. and to add 'transit_days' to result.
    """
    def fedex_rate_shipment(self, order):
        max_weight = self._fedex_convert_weight(self.fedex_default_packaging_id.max_weight, self.fedex_weight_unit)
        price = 0.0
        is_india = order.partner_shipping_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'

        # Estimate weight of the sales order; will be definitely recomputed on the picking field "weight"
        est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
        weight_value = self._fedex_convert_weight(est_weight_value, self.fedex_weight_unit)

        # Some users may want to ship very lightweight items; in order to give them a rating, we round the
        # converted weight of the shipping to the smallest value accepted by FedEx: 0.01 kg or lb.
        # (in the case where the weight is actually 0.0 because weights are not set, don't do this)
        if weight_value > 0.0:
            weight_value = max(weight_value, 0.01)

        order_currency = order.currency_id
        superself = self.sudo()

        # Hibou Delivery methods for collecting details in an overridable way
        shipper_company = superself.get_shipper_company(order=order)
        shipper_warehouse = superself.get_shipper_warehouse(order=order)
        recipient = superself.get_recipient(order=order)
        acc_number = superself._get_fedex_account_number(order=order)
        meter_number = superself._get_fedex_meter_number(order=order)
        order_name = superself.get_order_name(order=order)
        residential = self._get_fedex_recipient_is_residential(recipient)
        date_planned = None
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')

        # Authentication stuff
        srm = FedexRequest(self.log_xml, request_type="rating", prod_environment=self.prod_environment)
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(acc_number, meter_number)

        # Build basic rating request and set addresses
        srm.transaction_detail(order_name)
        srm.shipment_request(
            self.fedex_droppoff_type,
            self.fedex_service_type,
            self.fedex_default_packaging_id.shipper_package_code,
            self.fedex_weight_unit,
            self.fedex_saturday_delivery,
        )
        pkg = self.fedex_default_packaging_id

        srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
        srm.set_shipper(shipper_company, shipper_warehouse)
        srm.set_recipient(recipient, residential=residential)

        if max_weight and weight_value > max_weight:
            total_package = int(weight_value / max_weight)
            last_package_weight = weight_value % max_weight

            for sequence in range(1, total_package + 1):
                srm.add_package(
                    max_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=sequence,
                    mode='rating',
                )
            if last_package_weight:
                total_package = total_package + 1
                srm.add_package(
                    last_package_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=total_package,
                    mode='rating',
                )
            srm.set_master_package(weight_value, total_package)
        else:
            srm.add_package(
                weight_value,
                package_code=pkg.shipper_package_code,
                package_height=pkg.height,
                package_width=pkg.width,
                package_length=pkg.length,
                mode='rating',
            )
            srm.set_master_package(weight_value, 1)

        # Commodities for customs declaration (international shipping)
        if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or is_india:
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = order.warehouse_id.partner_id.country_id.code

            for line in order.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                commodity_amount = line.price_total / line.product_uom_qty
                total_commodities_amount += (commodity_amount * line.product_uom_qty)
                commodity_description = line.product_id.name
                commodity_number_of_piece = '1'
                commodity_weight_units = self.fedex_weight_unit
                commodity_weight_value = self._fedex_convert_weight(line.product_id.weight * line.product_uom_qty, self.fedex_weight_unit)
                commodity_quantity = line.product_uom_qty
                commodity_quantity_units = 'EA'
                # DO NOT FORWARD PORT AFTER 12.0
                if getattr(line.product_id, 'hs_code', False):
                    commodity_harmonized_code = line.product_id.hs_code or ''
                else:
                    commodity_harmonized_code = ''
                srm._commodities(_convert_curr_iso_fdx(order_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
            srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.warehouse_id.partner_id.country_id.code, superself.fedex_account_number)

        request = srm.rate(date_planned=date_planned)

        warnings = request.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if not request.get('errors_message'):
            if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
            else:
                _logger.info("Preferred currency has not been found in FedEx response")
                company_currency = order.company_id.currency_id
                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                    amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                    price = company_currency._convert(amount, order_currency, order.company_id, order.date_order or fields.Date.today())
                else:
                    amount = request['price']['USD']
                    price = company_currency._convert(amount, order_currency, order.company_id, order.date_order or fields.Date.today())
        else:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s') % request['errors_message'],
                    'warning_message': False}

        date_delivered = request.get('date_delivered', False)
        if date_delivered and 'delivery_calendar_id' in self and self.delivery_calendar_id.tz:
            tz = pytz.timezone(self.delivery_calendar_id.tz)
            date_delivered = tz.localize(date_delivered).astimezone(pytz.utc).replace(tzinfo=None)
        return {'success': True,
                'price': price,
                'error_message': False,
                'transit_days': request.get('transit_days', False),
                'date_delivered': date_delivered,
                'warning_message': _('Warning:\n%s') % warnings if warnings else False}

    """
    Overrides to use Hibou Delivery methods to get shipper etc. and add insurance.
    """
    def fedex_send_shipping(self, pickings):
        res = []

        for picking in pickings:
            srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
            superself = self.sudo()

            picking_packages = picking.package_ids
            package_carriers = picking_packages.mapped('carrier_id')
            if package_carriers:
                # only ship ours
                picking_packages = picking_packages.filtered(lambda p: p.carrier_id == self and not p.carrier_tracking_ref)

            if package_carriers and not picking_packages:
                continue

            shipper_company = superself.get_shipper_company(picking=picking)
            shipper_warehouse = superself.get_shipper_warehouse(picking=picking)
            recipient = superself.get_recipient(picking=picking)
            acc_number = superself._get_fedex_account_number(picking=picking)
            meter_number = superself._get_fedex_meter_number(picking=picking)
            payment_acc_number = superself._get_fedex_payment_account_number(picking=picking)
            order_name = superself.get_order_name(picking=picking)
            attn = superself.get_attn(picking=picking)
            residential = self._get_fedex_recipient_is_residential(recipient)

            srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
            srm.client_detail(acc_number, meter_number)

            # Not the actual reference.  Using `shipment_name` during `add_package` calls.
            srm.transaction_detail(picking.id)

            package_type = picking_packages and picking_packages[0].packaging_id.shipper_package_code or self.fedex_default_packaging_id.shipper_package_code
            srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit, self.fedex_saturday_delivery)
            srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
            srm.set_shipper(shipper_company, shipper_warehouse)
            srm.set_recipient(recipient, attn=attn, residential=residential)

            srm.shipping_charges_payment(payment_acc_number, third_party=bool(self.get_third_party_account(picking=picking)))

            # Commonly this needs to be modified, e.g. for doc tabs.  Do not want to have to patch this entire method.
            srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

            order = picking.sale_id
            company = shipper_company
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)

            # Commodities for customs declaration (international shipping)
            if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

                commodity_currency = order_currency
                total_commodities_amount = 0.0
                commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code

                for operation in picking.move_line_ids:
                    commodity_amount = operation.move_id.sale_line_id.price_unit or operation.product_id.lst_price
                    total_commodities_amount += (commodity_amount * operation.qty_done)
                    commodity_description = operation.product_id.name
                    commodity_number_of_piece = '1'
                    commodity_weight_units = self.fedex_weight_unit
                    commodity_weight_value = self._fedex_convert_weight(operation.product_id.weight * operation.qty_done, self.fedex_weight_unit)
                    commodity_quantity = operation.qty_done
                    commodity_quantity_units = 'EA'
                    # DO NOT FORWARD PORT AFTER 12.0
                    if getattr(operation.product_id, 'hs_code', False):
                        commodity_harmonized_code = operation.product_id.hs_code or ''
                    else:
                        commodity_harmonized_code = ''
                    srm._commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
                srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS")
                srm.duties_payment(shipper_warehouse.country_id.code, acc_number)

            package_count = len(picking_packages) or 1

            # For india picking courier is not accepted without this details in label.
            po_number = dept_number = False
            if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
                po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
                dept_number = 'BILL D/T: SENDER'

            # TODO RIM master: factorize the following crap

            ################
            # Multipackage #
            ################
            if package_count > 1:

                # Note: Fedex has a complex multi-piece shipping interface
                # - Each package has to be sent in a separate request
                # - First package is called "master" package and holds shipping-
                #   related information, including addresses, customs...
                # - Last package responses contains shipping price and code
                # - If a problem happens with a package, every previous package
                #   of the shipping has to be cancelled separately
                # (Why doing it in a simple way when the complex way exists??)

                master_tracking_id = False
                package_labels = []
                carrier_tracking_ref = ""

                for sequence, package in enumerate(picking_packages, start=1):

                    package_weight = self._fedex_convert_weight(package.shipping_weight, self.fedex_weight_unit)
                    packaging = package.packaging_id
                    packaging_code = packaging.shipper_package_code if (packaging.package_carrier_type == 'fedex' and packaging.shipper_package_code) else self.fedex_default_packaging_id.shipper_package_code

                    # Hibou Delivery
                    # Add more details to package.
                    srm._add_package(
                        package_weight,
                        package_code=packaging_code,
                        package_height=packaging.height,
                        package_width=packaging.width,
                        package_length=packaging.length,
                        sequence_number=sequence,
                        po_number=po_number,
                        dept_number=dept_number,
                        ref=('%s-%d' % (order_name, sequence)),
                        insurance=superself.get_insurance_value(picking=picking, package=package),
                        signature_required=superself.get_signature_required(picking=picking, package=package)
                    )
                    srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                    request = srm.process_shipment()
                    package_name = package.name or sequence

                    warnings = request.get('warnings_message')
                    if warnings:
                        _logger.info(warnings)

                    # First package
                    if sequence == 1:
                        if not request.get('errors_message'):
                            master_tracking_id = request['master_tracking_id']
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = request['tracking_number']
                        else:
                            raise UserError(request['errors_message'])

                    # Intermediary packages
                    elif sequence > 1 and sequence < package_count:
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))
                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                        else:
                            raise UserError(request['errors_message'])

                    # Last package
                    elif sequence == package_count:
                        # recuperer le label pdf
                        if not request.get('errors_message'):
                            package_labels.append((package_name, srm.get_label()))

                            if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                                carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                            else:
                                _logger.info("Preferred currency has not been found in FedEx response")
                                company_currency = picking.company_id.currency_id
                                if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                    amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())
                                else:
                                    amount = request['price']['USD']
                                    carrier_price = company_currency._convert(
                                        amount, order_currency, company, order.date_order or fields.Date.today())

                            carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']

                            logmessage = _("Shipment created into Fedex<br/>"
                                           "<b>Tracking Numbers:</b> %s<br/>"
                                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join([pl[0] for pl in package_labels]))
                            if self.fedex_label_file_type != 'PDF':
                                attachments = [('LabelFedex-%s.%s' % (pl[0], self.fedex_label_file_type), pl[1]) for pl in package_labels]
                            if self.fedex_label_file_type == 'PDF':
                                attachments = [('LabelFedex.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
                            picking.message_post(body=logmessage, attachments=attachments)
                            shipping_data = {'exact_price': carrier_price,
                                             'tracking_number': carrier_tracking_ref}
                            res = res + [shipping_data]
                        else:
                            raise UserError(request['errors_message'])

            # TODO RIM handle if a package is not accepted (others should be deleted)

            ###############
            # One package #
            ###############
            elif package_count == 1:
                packaging = picking_packages[:1].packaging_id or self.fedex_default_packaging_id
                packaging_code = packaging.shipper_package_code if packaging.package_carrier_type == 'fedex' else self.fedex_default_packaging_id.shipper_package_code
                srm._add_package(
                    net_weight,
                    package_code=packaging_code,
                    package_height=packaging.height,
                    package_width=packaging.width,
                    package_length=packaging.length,
                    po_number=po_number,
                    dept_number=dept_number,
                    ref=order_name,
                    insurance=superself.get_insurance_value(picking=picking, package=picking_packages[:1]),
                    signature_required=superself.get_signature_required(picking=picking, package=picking_packages[:1])
                )
                srm.set_master_package(net_weight, 1)

                # Ask the shipping to fedex
                request = srm.process_shipment()

                warnings = request.get('warnings_message')
                if warnings:
                    _logger.info(warnings)

                if not request.get('errors_message'):

                    if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                        carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                    else:
                        _logger.info("Preferred currency has not been found in FedEx response")
                        company_currency = picking.company_id.currency_id
                        if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                            amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())
                        else:
                            amount = request['price']['USD']
                            carrier_price = company_currency._convert(
                                amount, order_currency, company, order.date_order or fields.Date.today())

                    carrier_tracking_ref = request['tracking_number']
                    logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (
                        carrier_tracking_ref))

                    fedex_labels = [
                        ('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
                        for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                    picking.message_post(body=logmessage, attachments=fedex_labels)

                    shipping_data = {'exact_price': carrier_price,
                                     'tracking_number': carrier_tracking_ref}
                    res = res + [shipping_data]
                else:
                    raise UserError(request['errors_message'])

            ##############
            # No package #
            ##############
            else:
                raise UserError(_('No packages for this picking'))

        return res

    def fedex_rate_shipment_multi(self, order=None, picking=None, packages=None):
        if not packages:
            return self._fedex_rate_shipment_multi_package(order=order, picking=picking)
        else:
            rates = []
            for package in packages:
                rates += self._fedex_rate_shipment_multi_package(order=order, picking=picking, package=package)
            return rates

    def _fedex_rate_shipment_multi_package(self, order=None, picking=None, package=None):
        if order:
            max_weight = self._fedex_convert_weight(self.fedex_default_packaging_id.max_weight, self.fedex_weight_unit)
            is_india = order.partner_shipping_id.country_id.code == 'IN' and order.company_id.partner_id.country_id.code == 'IN'
            est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
            weight_value = self._fedex_convert_weight(est_weight_value, self.fedex_weight_unit)
            order_currency = order.currency_id
        elif not package:
            is_india = picking.partner_id.country_id.code == 'IN' and picking.company_id.partner_id.country_id.code == 'IN'
            est_weight_value = sum([(line.product_id.weight * (line.qty_done or line.product_uom_qty)) for line in picking.move_line_ids]) or 0.0
            weight_value = self._fedex_convert_weight(est_weight_value, self.fedex_weight_unit)
            order_currency = picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id
        else:
            is_india = picking.partner_id.country_id.code == 'IN' and picking.company_id.partner_id.country_id.code == 'IN'
            order_currency = picking.sale_id.currency_id if picking.sale_id else picking.company_id.currency_id
            est_weight_value = self._fedex_convert_weight(package.shipping_weight or package.weight)
            weight_value = self._fedex_convert_weight(est_weight_value, self.fedex_weight_unit)


        price = 0.0

        # Some users may want to ship very lightweight items; in order to give them a rating, we round the
        # converted weight of the shipping to the smallest value accepted by FedEx: 0.01 kg or lb.
        # (in the case where the weight is actually 0.0 because weights are not set, don't do this)
        if weight_value > 0.0:
            weight_value = max(weight_value, 0.01)

        superself = self.sudo()

        # Hibou Delivery methods for collecting details in an overridable way
        shipper_company = superself.get_shipper_company(order=order, picking=picking)
        shipper_warehouse = superself.get_shipper_warehouse(order=order, picking=picking)
        recipient = superself.get_recipient(order=order, picking=picking)
        acc_number = superself._get_fedex_account_number(order=order, picking=picking)
        meter_number = superself._get_fedex_meter_number(order=order, picking=picking)
        order_name = superself.get_order_name(order=order, picking=picking)
        insurance_value = superself.get_insurance_value(order=order, picking=picking, package=package)
        signature_required = superself.get_signature_required(order=order, picking=picking, package=package)
        residential = self._get_fedex_recipient_is_residential(recipient)
        date_planned = fields.Datetime.now()
        if self.env.context.get('date_planned'):
            date_planned = self.env.context.get('date_planned')

        # Authentication stuff
        srm = FedexRequest(self.log_xml, request_type="rating", prod_environment=self.prod_environment)
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(acc_number, meter_number)

        # Build basic rating request and set addresses
        srm.transaction_detail(order_name)

        # TODO what shipment requests can we make?
        # TODO package and main weights?
        # TODO need package & weight count to pass in
        srm.shipment_request(
            self.fedex_droppoff_type,
            None,  # because we want all of the rates back...
            self.fedex_default_packaging_id.shipper_package_code,
            self.fedex_weight_unit,
            self.fedex_saturday_delivery,
            ship_timestamp=date_planned,
        )
        pkg = self.fedex_default_packaging_id

        srm.set_currency(_convert_curr_iso_fdx(order_currency.name))
        srm.set_shipper(shipper_company, shipper_warehouse)
        srm.set_recipient(recipient, residential=residential)

        if order and max_weight and weight_value > max_weight:
            total_package = int(weight_value / max_weight)
            last_package_weight = weight_value % max_weight

            for sequence in range(1, total_package + 1):
                srm.add_package(
                    max_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=sequence,
                    mode='rating',
                )
            if last_package_weight:
                total_package = total_package + 1
                srm.add_package(
                    last_package_weight,
                    package_code=pkg.shipper_package_code,
                    package_height=pkg.height,
                    package_width=pkg.width,
                    package_length=pkg.length,
                    sequence_number=total_package,
                    mode='rating',
                )
            srm.set_master_package(weight_value, total_package)
        elif order:
            srm.add_package(
                weight_value,
                package_code=pkg.shipper_package_code,
                package_height=pkg.height,
                package_width=pkg.width,
                package_length=pkg.length,
                mode='rating',
            )
            srm.set_master_package(weight_value, 1)
        else:
            if package:
                package_weight = self._fedex_convert_weight(package.shipping_weight or package.weight, self.fedex_weight_unit)
                packaging = package.packaging_id
                package_code = package.packaging_id.shipper_package_code if packaging.package_carrier_type == 'fedex' else self.fedex_default_packaging_id.shipper_package_code

                srm.add_package(
                    package_weight,
                    mode='rating',
                    package_code=package_code,
                    package_height=packaging.height,
                    package_width=packaging.width,
                    package_length=packaging.length,
                    sequence_number=1,
                    # po_number=po_number,
                    # dept_number=dept_number,
                    ref=('%s-%d' % (order_name, 1)),
                    insurance=insurance_value,
                    signature_required=signature_required
                )
            else:
                # deliver all together...
                package_weight = self._fedex_convert_weight(picking.shipping_weight or picking.weight, self.fedex_weight_unit)
                packaging = self.fedex_default_packaging_id

                srm.add_package(
                    package_weight,
                    mode='rating',
                    package_code=packaging.shipper_package_code,
                    package_height=packaging.height,
                    package_width=packaging.width,
                    package_length=packaging.length,
                    sequence_number=1,
                    # po_number=po_number,
                    # dept_number=dept_number,
                    ref=('%s-%d' % (order_name, 1)),
                    insurance=insurance_value,
                    signature_required=signature_required
                )


        # Commodities for customs declaration (international shipping)
        # TODO Intestigate rating if needed...
        # if self.fedex_service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY'] or is_india:
        #     total_commodities_amount = 0.0
        #     commodity_country_of_manufacture = order.warehouse_id.partner_id.country_id.code
        #
        #     for line in order.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
        #         commodity_amount = line.price_total / line.product_uom_qty
        #         total_commodities_amount += (commodity_amount * line.product_uom_qty)
        #         commodity_description = line.product_id.name
        #         commodity_number_of_piece = '1'
        #         commodity_weight_units = self.fedex_weight_unit
        #         commodity_weight_value = self._fedex_convert_weight(line.product_id.weight * line.product_uom_qty,
        #                                                             self.fedex_weight_unit)
        #         commodity_quantity = line.product_uom_qty
        #         commodity_quantity_units = 'EA'
        #         # DO NOT FORWARD PORT AFTER 12.0
        #         if getattr(line.product_id, 'hs_code', False):
        #             commodity_harmonized_code = line.product_id.hs_code or ''
        #         else:
        #             commodity_harmonized_code = ''
        #         srm._commodities(_convert_curr_iso_fdx(order_currency.name), commodity_amount,
        #                          commodity_number_of_piece, commodity_weight_units, commodity_weight_value,
        #                          commodity_description, commodity_country_of_manufacture, commodity_quantity,
        #                          commodity_quantity_units, commodity_harmonized_code)
        #     srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
        #     srm.duties_payment(order.warehouse_id.partner_id.country_id.code, superself.fedex_account_number)

        request_list = srm.rate(date_planned=date_planned, multi=True)
        result = []
        for request in request_list:
            price = 0.0
            warnings = request.get('warnings_message')
            if warnings:
                _logger.info(warnings)

            if not request.get('errors_message'):
                if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                    price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                else:
                    _logger.info("Preferred currency has not been found in FedEx response")
                    company_currency = order.company_id.currency_id
                    if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                        amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                        price = company_currency._convert(amount, order_currency, order.company_id,
                                                          order.date_order or fields.Date.today())
                    else:
                        amount = request['price']['USD']
                        price = company_currency._convert(amount, order_currency, order.company_id,
                                                          order.date_order or fields.Date.today())
            else:
                result.append({'carrier': self,
                               'success': False,
                               'price': 0.0,
                               'error_message': _('Error:\n%s') % request['errors_message'],
                               'warning_message': False,
                               'service_code': request['service_code'],
                               })
            service_code = request['service_code']
            carrier = self.fedex_find_delivery_carrier_for_service(service_code)
            if carrier:
                date_delivered = request.get('date_delivered', False)
                if date_delivered:
                    tz = pytz.timezone(self.delivery_calendar_id.tz)
                    date_delivered = tz.localize(date_delivered).astimezone(pytz.utc).replace(tzinfo=None)
                result.append({'carrier': carrier,
                               'package': package or self.env['stock.quant.package'].browse(),
                               'success': True,
                               'price': price,
                               'error_message': False,
                               'transit_days': request.get('transit_days', False),
                               'date_delivered': date_delivered,
                               'date_planned': date_planned,
                               'warning_message': _('Warning:\n%s') % warnings if warnings else False,
                               'service_code': request['service_code'],
                               })
        return result

    def fedex_find_delivery_carrier_for_service(self, service_code):
        if self.fedex_service_type == service_code:
            return self
        # arbitrary decision, lets find the same account number
        carrier = self.search([('fedex_account_number', '=', self.fedex_account_number),
                               ('fedex_service_type', '=', service_code)
                               ], limit=1)
        return carrier

    def fedex_cancel_shipment(self, picking):
        request = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        request.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        acc_number = superself._get_fedex_account_number(picking=picking)
        meter_number = superself._get_fedex_meter_number(picking=picking)
        request.client_detail(acc_number, meter_number)
        request.transaction_detail(picking.id)

        master_tracking_id = picking.carrier_tracking_ref.split(',')[0]
        request.set_deletion_details(master_tracking_id)
        result = request.delete_shipment()

        warnings = result.get('warnings_message')
        if warnings:
            _logger.info(warnings)

        if result.get('delete_success') and not result.get('errors_message'):
            picking.message_post(body=_(u'Shipment N° %s has been cancelled' % master_tracking_id))
            picking.write({'carrier_tracking_ref': '',
                           'carrier_price': 0.0})
        else:
            raise UserError(result['errors_message'])
