# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import api, fields, models


def sale_planner_warehouse_ids(env, company):
    get_param = env['ir.config_parameter'].sudo().get_param
    warehouse_ids = get_param('sale.planner.warehouse_ids.%s' % (company.id, )) or []
    if warehouse_ids and isinstance(warehouse_ids, str):
        try:
            warehouse_ids = [int(i) for i in warehouse_ids.split(',')]
        except:
            warehouse_ids = []
    return warehouse_ids


def sale_planner_carrier_ids(env, company):
    get_param = env['ir.config_parameter'].sudo().get_param
    carrier_ids = get_param('sale.planner.carrier_ids.%s' % (company.id, )) or []
    if carrier_ids and isinstance(carrier_ids, str):
        try:
            carrier_ids = [int(c) for c in carrier_ids.split(',')]
        except:
            carrier_ids = []
    return carrier_ids


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_planner_warehouse_ids = fields.Many2many('stock.warehouse',
                                                  string='Sale Order Planner Warehouses',
                                                  compute='_compute_sale_planner_warehouse_ids',
                                                  inverse='_inverse_sale_planner_warehouse_ids')
    sale_planner_carrier_ids = fields.Many2many('delivery.carrier',
                                                string='Sale Order Planner Carriers',
                                                compute='_compute_sale_planner_carrier_ids',
                                                inverse='_inverse_sale_planner_carrier_ids')

    def _compute_sale_planner_warehouse_ids_ids(self):
        company = self.company_id or self.env.user.company_id
        return sale_planner_warehouse_ids(self.env, company)
    
    def _compute_sale_planner_carrier_ids_ids(self):
        company = self.company_id or self.env.user.company_id
        return sale_planner_carrier_ids(self.env, company)

    def _compute_sale_planner_warehouse_ids(self):
        for settings in self:
            warehouse_ids = settings._compute_sale_planner_warehouse_ids_ids()
            warehouses = self.env['stock.warehouse'].browse(warehouse_ids)
            settings.sale_planner_warehouse_ids = warehouses

    def _compute_sale_planner_carrier_ids(self):
        for settings in self:
            carrier_ids = settings._compute_sale_planner_carrier_ids_ids()
            carriers = self.env['delivery.carrier'].browse(carrier_ids)
            settings.sale_planner_carrier_ids = carriers

    def _inverse_sale_planner_warehouse_ids(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        company_id = self.company_id.id or self.env.user.company_id.id
        for settings in self:
            warehouse_ids = ','.join(str(i) for i in settings.sale_planner_warehouse_ids.ids)
            set_param('sale.planner.warehouse_ids.%s' % (company_id, ), warehouse_ids)

    def _inverse_sale_planner_carrier_ids(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        company_id = self.company_id.id or self.env.user.company_id.id
        for settings in self:
            carrier_ids = ','.join(str(i) for i in settings.sale_planner_carrier_ids.ids)
            set_param('sale.planner.carrier_ids.%s' % (company_id, ), carrier_ids)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['sale_planner_warehouse_ids'] = [(6, 0, self._compute_sale_planner_warehouse_ids_ids())]
        res['sale_planner_carrier_ids'] = [(6, 0, self._compute_sale_planner_carrier_ids_ids())]
        return res
