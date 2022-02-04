# © 2021 Hibou Corp.

from datetime import datetime, timedelta
from logging import getLogger
from contextlib import contextmanager

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ...components.api.amazon import WrappedAPI

_logger = getLogger(__name__)

IMPORT_DELTA_BUFFER = 600  # seconds


class AmazonBackend(models.Model):
    _name = 'amazon.backend'
    _description = 'Amazon Backend'
    _inherit = 'connector.backend'

    name = fields.Char(string='Name')
    active = fields.Boolean(default=True)

    api_refresh_token = fields.Text(string='API Refresh Token', required=True)
    api_lwa_client_id = fields.Char(string='API LWA Client ID', required=True)
    api_lwa_client_secret = fields.Char(string='API LWA Client Secret', required=True)
    api_aws_access_key = fields.Char(string='API AWS Access Key', required=True)
    api_aws_secret_key = fields.Char(string='API AWS Secret Key', required=True)
    api_role_arn = fields.Char(string='API AWS Role ARN', required=True)

    merchant_id = fields.Char(string='Amazon Merchant Identifier', required=True)

    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Warehouses',
        required=True,
        help='Warehouses to use for delivery and stock.',
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
        'field on the sale order created by the connector.'
    )
    team_id = fields.Many2one('crm.team', string='Sales Team')
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help='Default Salesperson for newly imported orders.')
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'AMZ-', the sales "
             "order 112-5571768504079 in Amazon, will be named 'AMZ-112-5571768504079' "
             "in Odoo.",
    )
    payment_mode_id = fields.Many2one('account.payment.mode', string='Payment Mode')
    carrier_id = fields.Many2one('delivery.carrier', string='Delivery Method')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    buffer_qty = fields.Integer(string='Buffer Quantity',
                                help='Stock to hold back from Amazon for listings.',
                                default=0)

    fba_warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='amazon_backend_fba_stock_warehouse_rel',
        string='FBA Warehouses',
        required=False,
        help='Warehouses to use for FBA delivery and stock.',
    )
    fba_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='FBA Fiscal Position',
        help='Fiscal position to use on FBA orders.',
    )
    fba_analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='FBA Analytic account',
        help='If specified, this analytic account will be used to fill the '
        'field on the sale order created by the connector.'
    )
    fba_team_id = fields.Many2one('crm.team', string='FBA Sales Team')
    fba_user_id = fields.Many2one('res.users', string='FBA Salesperson',
                              help='Default Salesperson for newly imported FBA orders.')
    fba_sale_prefix = fields.Char(
        string='FBA Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'FBA-', the sales "
             "order 112-5571768504079 in Amazon, will be named 'FBA-112-5571768504079' "
             "in Odoo.",
    )
    fba_payment_mode_id = fields.Many2one('account.payment.mode', string='FBA Payment Mode')
    fba_carrier_id = fields.Many2one('delivery.carrier', string='FBA Delivery Method')
    fba_pricelist_id = fields.Many2one('product.pricelist', string='FBA Pricelist')
    fba_buffer_qty = fields.Integer(string='FBA Buffer Quantity',
                                    help='Stock to hold back from Amazon for FBA listings.',
                                    default=0)

    # New Product fields.
    product_categ_id = fields.Many2one(comodel_name='product.category', string='Product Category',
                                       help='Default product category for newly created products.')

    # Automation
    scheduler_order_import_running = fields.Boolean(string='Automatic Sale Order Import is Running',
                                                    compute='_compute_scheduler_running',
                                                    compute_sudo=True)
    scheduler_order_import = fields.Boolean(string='Automatic Sale Order Import')

    scheduler_product_inventory_export_running = fields.Boolean(string='Automatic Product Inventory Export is Running',
                                                                compute='_compute_scheduler_running',
                                                                compute_sudo=True)
    scheduler_product_inventory_export = fields.Boolean(string='Automatic Product Inventory Export')

    scheduler_product_price_export_running = fields.Boolean(string='Automatic Product Price Export is Running',
                                                            compute='_compute_scheduler_running',
                                                            compute_sudo=True)
    scheduler_product_price_export = fields.Boolean(string='Automatic Product Price Export')

    import_orders_from_date = fields.Datetime(
        string='Import sale orders from date',
    )

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        amazon_api = self.get_wrapped_api()
        with super().work_on(model_name, amazon_api=amazon_api, **kwargs) as work:
            yield work

    def button_test(self):
        self.ensure_one()
        amazon_api = self.get_wrapped_api()
        Shipping = amazon_api.shipping()
        raise UserError(str(Shipping.get_account()))

    def get_wrapped_api(self):
        self.ensure_one()
        return WrappedAPI(self.env,
                          self.api_refresh_token,
                          self.api_lwa_client_id,
                          self.api_lwa_client_secret,
                          self.api_aws_access_key,
                          self.api_aws_secret_key,
                          self.api_role_arn)

    def _compute_scheduler_running(self):
        sched_action_so_imp = self.env.ref('connector_amazon_sp.ir_cron_import_sale_orders', raise_if_not_found=False)
        sched_action_pi_exp = self.env.ref('connector_amazon_sp.ir_cron_export_product_inventory', raise_if_not_found=False)
        sched_action_pp_exp = self.env.ref('connector_amazon_sp.ir_cron_export_product_price', raise_if_not_found=False)
        for backend in self:
            backend.scheduler_order_import_running = bool(sched_action_so_imp and sched_action_so_imp.active)
            backend.scheduler_product_inventory_export_running = bool(sched_action_pi_exp and sched_action_pi_exp.active)
            backend.scheduler_product_price_export_running = bool(sched_action_pp_exp and sched_action_pp_exp.active)

    @api.model
    def _scheduler_import_sale_orders(self):
        # potential hook for customization (e.g. pad from date or provide its own)
        backends = self.search([
            ('scheduler_order_import', '=', True),
        ])
        return backends.import_sale_orders()

    @api.model
    def _scheduler_export_product_inventory(self):
        backends = self.search([
            ('scheduler_product_inventory_export', '=', True),
        ])
        for backend in backends:
            self.env['amazon.product.product'].update_inventory(backend)

    @api.model
    def _scheduler_export_product_price(self):
        backends = self.search([
            ('scheduler_product_price_export', '=', True),
        ])
        for backend in backends:
            self.env['amazon.product.product'].update_price(backend)

    @api.multi
    def import_sale_orders(self):
        self._import_from_date('amazon.sale.order', 'import_orders_from_date')
        return True

    @api.multi
    def _import_from_date(self, model_name, from_date_field):
        import_start_time = datetime.now().replace(microsecond=0) - timedelta(seconds=IMPORT_DELTA_BUFFER)
        for backend in self:
            from_date = backend[from_date_field]
            if from_date:
                from_date = fields.Datetime.from_string(from_date)
            else:
                from_date = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)

            self.env[model_name].with_delay(priority=5).import_batch(
                backend,
                # TODO which filters can we use in Amazon?
                filters={'CreatedAfter': from_date.isoformat(),
                         'CreatedBefore': import_start_time.isoformat()}
            )
            # We add a buffer, but won't import them twice.
            # NOTE this is 2x the offset from now()
            next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
            next_time = fields.Datetime.to_string(next_time)
            backend.write({from_date_field: next_time})
