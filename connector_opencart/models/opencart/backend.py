# © 2019-2021 Hibou Corp.


from logging import getLogger
from contextlib import contextmanager
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ...components.api.opencart import Opencart

_logger = getLogger(__name__)


class OpencartBackend(models.Model):
    _name = 'opencart.backend'
    _description = 'Opencart Backend'
    _inherit = 'connector.backend'

    name = fields.Char(string='Name')
    base_url = fields.Char(
        string='Base URL',
        required=True,
        help='Url of your site, e.g. http://your-site.com',
    )
    restadmin_token = fields.Char(
        string='RestAdmin Token',
        required=True,
        help='configured in Extensions->Modules->RestAdminAPI',
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse to use for stock.',
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
        help='Fiscal position to use on orders.',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        help='If specified, this analytic account will be used to fill the '
        'field  on the sale order created by the connector.'
    )
    team_id = fields.Many2one(comodel_name='crm.team', string='Sales Team')
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'OC-', the sales "
             "order 36071 in Opencart, will be named 'OC-36071' "
             "in Odoo.",
    )
    coupon_product_id = fields.Many2one(comodel_name='product.product', string='Coupon Product',
                                        help='Product to represent coupon discounts.')

    # New Product fields.
    product_categ_id = fields.Many2one(comodel_name='product.category', string='Product Category',
                                       help='Default product category for newly created products.')

    # renamed, and not used when searching orders anymore
    import_orders_after_id = fields.Integer(
        string='Highest Order ID',
    )
    # Note that Opencart may not return timestamps in UTC
    import_orders_after_date = fields.Datetime(
        string='Import Orders Modified After',
    )
    server_offset_hours = fields.Float(
        string='Opencart Server Timezone Offset',
        help='E.g. US Pacific is -8.0, the important thing is to either not change this during DST or to adjust the import_orders_after_date field at the same time.',
    )

    so_require_product_setup = fields.Boolean(string='SO Require Product Setup',
                                              help='Prevents SO from being confirmed (failed queue job), if one or more products has an open checkpoint.')

    scheduler_order_import_running = fields.Boolean(string='Auctomatic Sale Order Import is Running',
                                                    compute='_compute_scheduler_order_import_running',
                                                    compute_sudo=True)
    scheduler_order_import = fields.Boolean(string='Automatic Sale Order Import',
                                            help='Individual stores should also be enabled for import.')

    def _compute_scheduler_order_import_running(self):
        sched_action = self.env.ref('connector_opencart.ir_cron_import_sale_orders', raise_if_not_found=False)
        for backend in self:
            backend.scheduler_order_import_running = bool(sched_action.active)

    @contextmanager
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        opencart_api = Opencart(self.base_url, self.restadmin_token)
        _super = super(OpencartBackend, self)
        with _super.work_on(model_name, opencart_api=opencart_api, **kwargs) as work:
            yield work

    def add_checkpoint(self, record, summary=''):
        self.ensure_one()
        record.ensure_one()
        user = self.env.user
        summary = summary or self.env.context.get('checkpoint_summary', '')
        if 'user_id' in record and record.user_id:
            user = record.user_id
        if 'odoo_id' in record:
            return record.odoo_id.activity_schedule(
                act_type_xmlid='connector_opencart.checkpoint',
                summary=summary,
                user_id=user.id)
        return record.activity_schedule(
            act_type_xmlid='connector_opencart.checkpoint',
            summary=summary,
            user_id=user.id)

    def find_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        if 'odoo_id' in record:
            return record.odoo_id.activity_search(act_type_xmlids='connector_opencart.checkpoint')
        return record.activity_search(act_type_xmlids='connector_opencart.checkpoint')

    def synchronize_metadata(self):
        try:
            for backend in self:
                self.env['opencart.store'].import_batch(backend)
            return True
        except Exception as e:
            _logger.error(e)
            raise UserError(_("Check your configuration, we can't get the data. "
                              "Here is the error:\n%s") % (e, ))

    @api.model
    def _scheduler_import_sale_orders(self):
        # potential hook for customization (e.g. pad from date or provide its own)
        backends = self.search([
            ('base_url', '!=', False),
            ('restadmin_token', '!=', False),
            ('import_orders_after_date', '!=', False),
            ('scheduler_order_import', '=', True),
        ])
        return backends.import_sale_orders()

    def import_sale_orders(self):
        self._import_sale_orders_after_date()
        return True

    def _import_after_id(self, model_name, after_id_field):
        for backend in self:
            after_id = backend[after_id_field]
            self.env[model_name].with_delay().import_batch(
                backend,
                filters={'after_id': after_id}
            )

    def _import_sale_orders_after_date(self):
        for backend in self:
            date = backend.date_to_opencart(backend.import_orders_after_date)
            date = str(date).replace(' ', 'T')
            self.env['opencart.sale.order'].with_delay().import_batch(
                backend,
                filters={'modified_from': date}
            )

    def date_to_opencart(self, date):
        # date provided should be UTC and will be converted to Opencart's dates
        return self._date_plus_hours(date, self.server_offset_hours or 0)

    def date_to_odoo(self, date):
        # date provided should be in Opencart's TZ, converted to UTC
        return self._date_plus_hours(date, -(self.server_offset_hours or 0))

    def _date_plus_hours(self, date, hours):
        if not hours:
            return date
        if isinstance(date, str):
            date = fields.Datetime.from_string(date)
        return date + timedelta(hours=hours)
