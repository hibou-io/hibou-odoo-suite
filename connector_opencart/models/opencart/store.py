# © 2019-2021 Hibou Corp.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError


class OpencartStore(models.Model):
    _name = 'opencart.store'
    _inherit = ['opencart.binding']
    _description = 'Opencart Store'
    _parent_name = 'backend_id'

    name = fields.Char()
    backend_id = fields.Many2one('opencart.backend',
                                 string='Opencart Backend',
                                 ondelete='cascade',
                                 readonly=True)

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help='Warehouse to use for stock. (overridden from backend)',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='warehouse_id.company_id',
        string='Company',
        readonly=True,
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        help='Fiscal position to use on orders. (overridden from backend)',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        help='If specified, this analytic account will be used to fill the '
        'field  on the sale order created by the connector. (overridden from backend)'
    )
    team_id = fields.Many2one(comodel_name='crm.team', string='Sales Team',
                              help='(overridden from backend)')
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'OC-', the sales "
             "order 36071 in Opencart, will be named 'OC-36071' "
             "in Odoo. (overridden from backend)",
    )
    coupon_product_id = fields.Many2one(comodel_name='product.product', string='Coupon Product',
                                        help='Product to represent coupon discounts.')
    enable_order_import = fields.Boolean(string='Enable Sale Order Import', default=True,
                                         help='If not enabled, then stores will be skipped during order imiport.')


class OpencartStoreAdapter(Component):
    _name = 'opencart.store.adapter'
    _inherit = 'opencart.adapter'
    _apply_on = 'opencart.store'

    def search(self, filters=None):
        api_instance = self.api_instance
        stores_response = api_instance.stores.all()
        if 'error' in stores_response and stores_response['error']:
            raise ValidationError(str(stores_response))

        if 'data' not in stores_response or not isinstance(stores_response['data'], list):
            return []

        stores = stores_response['data']
        return list(map(lambda s: s['store_id'], stores))

    def read(self, id):
        api_instance = self.api_instance
        record = api_instance.stores.get(id)
        if 'data' in record and record['data']:
            return record['data']
        raise RetryableJobError('Store "' + str(id) + '" did not return an store response. ' + str(record))
