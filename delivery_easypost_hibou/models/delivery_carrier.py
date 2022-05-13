import requests
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.delivery_easypost.models.easypost_request import EasypostRequest


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    easypost_return_method = fields.Selection([
        ('ep', 'EasyPost Return'),
        ('swap', 'Swap Addresses')
    ], string='Return Method', default='ep')

    def easypost_send_shipping(self, pickings):
        """ It creates an easypost order and buy it with the selected rate on
        delivery method or cheapest rate if it is not set. It will use the
        packages used with the put in pack functionality or a single package if
        the user didn't use packages.
        Once the order is purchased. It will post as message the tracking
        links and the shipping labels.
        """
        superself = self.sudo()
        
        res = []
        ep = EasypostRequest(self.sudo().easypost_production_api_key if self.prod_environment else self.sudo().easypost_test_api_key, self.log_xml)
        for picking in pickings:
            # Call Hibou delivery method to get picking type
            if self.easypost_return_method == 'ep':
                is_return = superself._classify_picking(picking) in ('in', 'dropship_in',)
                result = ep.send_shipping(self, picking.partner_id, picking.picking_type_id.warehouse_id.partner_id,
                                          picking=picking, is_return=is_return)
            else:
                shipper = superself.get_shipper_warehouse(picking=picking)
                recipient = superself.get_recipient(picking=picking)
                result = ep.send_shipping(self, recipient, shipper, picking=picking)
            
            if result.get('error_message'):
                raise UserError(result['error_message'])
            rate = result.get('rate')
            if rate['currency'] == picking.company_id.currency_id.name:
                price = float(rate['rate'])
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', rate['currency'])], limit=1)
                price = quote_currency._convert(float(rate['rate']), picking.company_id.currency_id, self.env.company, fields.Date.today())

            # return tracking information
            carrier_tracking_link = ""
            for track_number, tracker_url in result.get('track_shipments_url').items():
                carrier_tracking_link += '<a href=' + tracker_url + '>' + track_number + '</a><br/>'

            carrier_tracking_ref = ' + '.join(result.get('track_shipments_url').keys())

            labels = []
            for track_number, label_url in result.get('track_label_data').items():
                label = requests.get(label_url)
                labels.append(('LabelEasypost-%s.%s' % (track_number, self.easypost_label_file_type), label.content))

            logmessage = _("Shipment created into Easypost<br/>"
                           "<b>Tracking Numbers:</b> %s<br/>") % (carrier_tracking_link)
            if picking.sale_id:
                for pick in picking.sale_id.picking_ids:
                    pick.message_post(body=logmessage, attachments=labels)
            else:
                picking.message_post(body=logmessage, attachments=labels)

            shipping_data = {'exact_price': price,
                             'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            # store order reference on picking
            picking.ep_order_ref = result.get('id')
            if picking.carrier_id.return_label_on_delivery:
                self.get_return_label(picking)
        return res
