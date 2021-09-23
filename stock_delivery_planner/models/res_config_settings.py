# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_delivery_planner_base_carrier_ids = fields.Many2many('delivery.carrier',
                                                               string='Delivery Planner Base Carriers',
                                                               compute='_compute_stock_delivery_planner_base_carrier_ids',
                                                               inverse='_inverse_stock_delivery_planner_base_carrier_ids')

    def _compute_stock_delivery_planner_base_carrier_ids_ids(self):
        # used to compute the field and update in get_values
        get_param = self.env['ir.config_parameter'].sudo().get_param
        company_id = self.company_id.id or self.env.company.id
        carrier_ids = get_param('stock.delivery.planner.carrier_ids.%s' % (company_id,)) or []
        if carrier_ids and isinstance(carrier_ids, str):
            try:
                carrier_ids = [int(c) for c in carrier_ids.split(',')]
            except:
                carrier_ids = []
        return carrier_ids

    def _compute_stock_delivery_planner_base_carrier_ids(self):
        for settings in self:
            carrier_ids = settings._compute_stock_delivery_planner_base_carrier_ids_ids()
            carriers = self.env['delivery.carrier'].browse(carrier_ids)
            settings.stock_delivery_planner_base_carrier_ids = carriers

    def _inverse_stock_delivery_planner_base_carrier_ids(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        company_id = self.company_id.id or self.env.company.id
        for settings in self:
            carrier_ids = ','.join(str(i) for i in settings.stock_delivery_planner_base_carrier_ids.ids)
            set_param('stock.delivery.planner.carrier_ids.%s' % (company_id, ), carrier_ids)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['stock_delivery_planner_base_carrier_ids'] = [(6, 0, self._compute_stock_delivery_planner_base_carrier_ids_ids())]
        return res
