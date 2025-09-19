from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    shipping_account_ids = fields.One2many('partner.shipping.account', 'partner_id', string='Shipping Accounts')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shipping_account_id = fields.Many2one('partner.shipping.account', string='Shipping Account')


class PartnerShippingAccount(models.Model):
    _name = 'partner.shipping.account'
    _description = 'Partner Shipping Account'

    name = fields.Char(string='Account Num.', required=True)
    description = fields.Char(string='Description')
    partner_id = fields.Many2one('res.partner', string='Partner', help='Leave blank to allow as a generic 3rd party shipper.')
    delivery_type = fields.Selection([
        ('other', 'Other'),
    ], string='Carrier', required=True, default='other')
    note = fields.Text(string='Internal Note')

    def _compute_display_name(self):
        delivery_types = self._fields['delivery_type']._description_selection(self.env)

        def get_name(value):
            name = [n for v, n in delivery_types if v == value]
            return name[0] if name else 'Undefined'

        for acc in self:
            if acc.description:
                acc.display_name = acc.description
            else:
                acc.display_name = '%s: %s' % (get_name(acc.delivery_type), acc.name)

    @api.constrains('name', 'delivery_type')
    def _check_validity(self):
        for acc in self:
            check = getattr(acc, acc.delivery_type + '_check_validity', None)
            if check:
                return check()
