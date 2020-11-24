from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .gls_nl_request import GLSNLRequest
from requests import HTTPError
from base64 import decodebytes
from csv import reader as csv_reader


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    package_carrier_type = fields.Selection(selection_add=[('gls_nl', 'GLS Netherlands')])


class ProviderGLSNL(models.Model):
    _inherit = 'delivery.carrier'

    GLS_NL_SOFTWARE_NAME = 'Odoo'
    GLS_NL_SOFTWARE_VER = '12.0'
    GLS_NL_COUNTRY_NOT_FOUND = 'GLS_NL_COUNTRY_NOT_FOUND'

    delivery_type = fields.Selection(selection_add=[('gls_nl', 'GLS Netherlands')])

    gls_nl_username = fields.Char(string='GLS NL Username', groups='base.group_system')
    gls_nl_password = fields.Char(string='GLS NL Password', groups='base.group_system')
    gls_nl_labeltype = fields.Selection([
        ('zpl', 'ZPL'),
        ('pdf', 'PDF'),
    ], string='GLS NL Label Type')
    gls_nl_express = fields.Selection([
        ('t9', 'Delivery before 09:00 on weekdays'),
        ('t12', 'Delivery before 12:00 on weekdays'),
        ('t17', 'Delivery before 17:00 on weekdays'),
        ('s9', 'Delivery before 09:00 on Saturday'),
        ('s12', 'Delivery before 12:00 on Saturday'),
        ('s17', 'Delivery before 17:00 on Saturday'),
    ], string='GLS NL Express', help='Express service tier (leave blank for regular)')
    gls_nl_rate_id = fields.Many2one('ir.attachment', string='GLS NL Rates')

    def button_gls_nl_test_rates(self):
        self.ensure_one()
        if not self.gls_nl_rate_id:
            raise UserError(_('No GLS NL Rate file is attached.'))
        rate_data = self._gls_nl_process_rates()
        weight_col_count = len(rate_data['w'])
        row_count = len(rate_data['r'])
        country_col = rate_data['c']
        country_model = self.env['res.country']
        for row in rate_data['r']:
            country = country_model.search([('code', '=', row[country_col])], limit=1)
            if not country:
                raise ValidationError(_('Could not locate country by code: "%s" for row: %s') % (row[country_col], row))
            for w, i in rate_data['w'].items():
                try:
                    cost = float(row[i])
                except ValueError:
                    raise ValidationError(_('Could not process cost for row: %s') % (row, ))
        raise ValidationError(_('Looks good! %s weights, %s countries located.') % (weight_col_count, row_count))

    def _gls_nl_process_rates(self):
        """
        'w' key will be weights to row index map
        'c' key will be the country code index
        'r' key will be rows from the original that can use indexes above
        :return:
        """
        datab = decodebytes(self.gls_nl_rate_id.datas)
        csv_data = datab.decode()
        csv_data = csv_data.replace('\r', '')
        csv_lines = csv_data.splitlines()
        header = [csv_lines[0]]
        body = csv_lines[1:]
        data = {'w': {}, 'r': []}
        for row in csv_reader(header):
            for i, col in enumerate(row):
                if col == 'Country':
                    data['c'] = i
                else:
                    try:
                        weight = float(col)
                        data['w'][weight] = i
                    except ValueError:
                        pass
        if 'c' not in data:
            raise ValidationError(_('Could not locate "Country" column.'))
        if not data['w']:
            raise ValidationError(_('Could not locate any weight columns.'))
        for row in csv_reader(body):
            data['r'].append(row)
        return data

    def _gls_nl_rate(self, country_code, weight):
        if weight < 0.0:
            return 0.0
        rate_data = self._gls_nl_process_rates()
        country_col = rate_data['c']
        rate = None
        country_found = False
        for row in rate_data['r']:
            if row[country_col] == country_code:
                country_found = True
                for w, i in rate_data['w'].items():
                    if weight <= w:
                        try:
                            rate = float(row[i])
                            break
                        except ValueError:
                            pass
                else:
                    # our w, i will be the last weight and rate.
                    try:
                        # Return Max rate + remaining weight rated
                        return float(row[i]) + self._gls_nl_rate(country_code, weight-w)
                    except ValueError:
                        pass
                break
        if rate is None and not country_found:
            return self.GLS_NL_COUNTRY_NOT_FOUND
        return rate

    def gls_nl_rate_shipment(self, order):
        recipient = self.get_recipient(order=order)
        rate = None
        dest_country = recipient.country_id.code
        est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
        if dest_country:
            rate = self._gls_nl_rate(dest_country, est_weight_value)

        # Handle errors and rate conversions.
        error_message = None
        if not dest_country or rate == self.GLS_NL_COUNTRY_NOT_FOUND:
            error_message = _('Destination country not found: "%s"') % (dest_country, )
        if rate is None or error_message:
            if not error_message:
                error_message = _('Rate not found for weight: "%s"') % (est_weight_value, )
            return {'success': False,
                    'price': 0.0,
                    'error_message': error_message,
                    'warning_message': False}

        euro_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
        if euro_currency and order.currency_id and euro_currency != order.currency_id:
            rate = euro_currency._convert(rate,
                                          order.currency_id,
                                          order.company_id,
                                          order.date_order or fields.Date.today())

        return {'success': True,
                'price': rate,
                'error_message': False,
                'warning_message': False}

    def _get_gls_nl_service(self):
        return GLSNLRequest(self.prod_environment)

    def _gls_nl_make_address(self, partner):
        # Addresses look like
        # {
        #   'name1': '',
        #   'name2': '',
        #   'name3': '',
        #   'street': '',
        #   'houseNo': '',
        #   'houseNoExt': '',
        #   'zipCode': '',
        #   'city': '',
        #   'countrycode': '',
        #   'contact': '',
        #   'phone': '',
        #   'email': '',
        # }
        address = {}
        pieces = partner.street.split(' ')
        street = ' '.join(pieces[:-1]).strip(' ,')
        house = pieces[-1]
        address['name1'] = partner.name
        address['street'] = street
        address['houseNo'] = house
        if partner.street2:
            address['houseNoExt'] = partner.street2
        address['zipCode'] = partner.zip
        address['city'] = partner.city
        address['countrycode'] = partner.country_id.code
        if partner.phone:
            address['phone'] = partner.phone
        if partner.email:
            address['email'] = partner.email
        return address

    def gls_nl_send_shipping(self, pickings):
        res = []
        sudoself = self.sudo()
        service = sudoself._get_gls_nl_service()

        for picking in pickings:
            #company = self.get_shipper_company(picking=picking)  # Requester not needed currently
            from_ = self.get_shipper_warehouse(picking=picking)
            to = self.get_recipient(picking=picking)
            total_rate = 0.0

            request_body = {
                'labelType': sudoself.gls_nl_labeltype,
                'username': sudoself.gls_nl_username,
                'password': sudoself.gls_nl_password,
                'shiptype': 'p',  # note not shipType, 'f' for Freight
                'trackingLinkType': 's',
                # 'customerNo': '',  # needed if there are more 'customer numbers' attached to a single MyGLS API Account
                'reference': picking.name,
                'addresses': {
                    'pickupAddress': self._gls_nl_make_address(from_),
                    'deliveryAddress': self._gls_nl_make_address(to),
                    #'requesterAddress': {},  # Not needed currently
                },
                'units': [],
                'services': {},
                'shippingDate': fields.Date.to_string(fields.Date.today()),
                'shippingSystemName': self.GLS_NL_SOFTWARE_NAME,
                'shippingSystemVersion': self.GLS_NL_SOFTWARE_VER,
            }

            if sudoself.gls_nl_express:
                request_body['services']['expressService'] = sudoself.gls_nl_express

            # Build out units
            # Units look like:
            # {
            #   'unitId': 'A',
            #   'unitType': '',  # only for freight
            #   'weight': 0.0,
            #   'additionalInfo1': '',
            #   'additionalInfo2': '',
            # }
            if picking.package_ids:
                for package in picking.package_ids:
                    converted_weight = self._gls_convert_weight(package.shipping_weight)
                    rate = self._gls_nl_rate(to.country_id.code, converted_weight or 0.0)
                    if rate and rate != self.GLS_NL_COUNTRY_NOT_FOUND:
                        total_rate += rate
                    unit = {
                        'unitId': package.name,
                        'weight': converted_weight
                    }
                    request_body['units'].append(unit)
            else:
                converted_weight = self._gls_convert_weight(picking.shipping_weight)
                rate = self._gls_nl_rate(to.country_id.code, converted_weight or 0.0)
                if rate and rate != self.GLS_NL_COUNTRY_NOT_FOUND:
                    total_rate += rate
                unit = {
                    'unitId': picking.name,
                    'weight': converted_weight,
                }
                request_body['units'].append(unit)

            try:
                # Create label
                label = service.create_label(request_body)
                trackings = []
                uniq_nos = []
                attachments = []
                for i, unit in enumerate(label['units'], 1):
                    trackings.append(unit['unitNo'])
                    uniq_nos.append(unit['uniqueNo'])
                    attachments.append(('LabelGLSNL-%s-%s.%s' % (unit['unitNo'], i, sudoself.gls_nl_labeltype), unit['label']))

                tracking = ', '.join(set(trackings))
                logmessage = _("Shipment created into GLS NL<br/>"
                               "<b>Tracking Number:</b> %s<br/>"
                               "<b>UniqueNo:</b> %s") % (tracking, ', '.join(set(uniq_nos)))
                picking.message_post(body=logmessage, attachments=attachments)
                shipping_data = {'exact_price': total_rate, 'tracking_number': tracking}
                res.append(shipping_data)
            except HTTPError as e:
                raise ValidationError(e)
        return res

    def gls_nl_get_tracking_link(self, pickings):
        return 'https://gls-group.eu/EU/en/parcel-tracking?match=%s' % pickings.carrier_tracking_ref

    def gls_nl_cancel_shipment(self, picking):
        sudoself = self.sudo()
        service = sudoself._get_gls_nl_service()
        try:
            request_body = {
                'unitNo': picking.carrier_tracking_ref,
                'username': sudoself.gls_nl_username,
                'password': sudoself.gls_nl_password,
                'shiptype': 'p',
                'shippingSystemName': self.GLS_NL_SOFTWARE_NAME,
                'shippingSystemVersion': self.GLS_NL_SOFTWARE_VER,
            }
            service.delete_label(request_body)
            picking.message_post(body=_('Shipment N° %s has been cancelled' % picking.carrier_tracking_ref))
            picking.write({'carrier_tracking_ref': '', 'carrier_price': 0.0})
        except HTTPError as e:
            raise ValidationError(e)

    def _gls_convert_weight(self, weight):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        product_weight_in_lbs_param = get_param('product.weight_in_lbs')
        if product_weight_in_lbs_param == '1':
            return weight / 2.20462
        else:
            return weight
