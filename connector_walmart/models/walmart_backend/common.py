# © 2017,2018 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta
from logging import getLogger
from contextlib import contextmanager

from odoo import api, fields, models, _
from ...components.api.walmart import Walmart

_logger = getLogger(__name__)

IMPORT_DELTA_BUFFER = 600  # seconds


class WalmartBackend(models.Model):
    _name = 'walmart.backend'
    _description = 'Walmart Backend'
    _inherit = 'connector.backend'

    name = fields.Char(string='Name')
    client_id = fields.Char(string='Client ID')
    client_secret = fields.Char(string='Client Secret')
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
    user_id = fields.Many2one(comodel_name='res.users', string='Salesperson',
                              help="Default Salesperson for newly imported orders.")
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'WMT-', the sales "
             "order 5571768504079 in Walmart, will be named 'WMT-5571768504079' "
             "in Odoo.",
    )
    payment_mode_id = fields.Many2one(comodel_name='account.payment.mode', string="Payment Mode")

    # New Product fields.
    product_categ_id = fields.Many2one(comodel_name='product.category', string='Product Category',
                                       help='Default product category for newly created products.')

    acknowledge_order = fields.Selection([
        ('never', 'Never'),
        ('order_create', 'On Order Import'),
        ('order_confirm', 'On Order Confirmation'),
    ], string='Acknowledge Order')


    import_orders_from_date = fields.Datetime(
        string='Import sale orders from date',
    )

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        walmart_api = Walmart(self.client_id, self.client_secret)
        _super = super(WalmartBackend, self)
        with _super.work_on(model_name, walmart_api=walmart_api, **kwargs) as work:
            yield work

    @api.model
    def _scheduler_import_sale_orders(self):
        # potential hook for customization (e.g. pad from date or provide its own)
        backends = self.search([
            ('client_id', '!=', False),
            ('client_secret', '!=', False),
            ('import_orders_from_date', '!=', False),
        ])
        return backends.import_sale_orders()

    @api.multi
    def import_sale_orders(self):
        self._import_from_date('walmart.sale.order', 'import_orders_from_date')
        return True

    @api.multi
    def _import_from_date(self, model_name, from_date_field):
        import_start_time = datetime.now()
        for backend in self:
            from_date = backend[from_date_field]
            if from_date:
                from_date = fields.Datetime.from_string(from_date)
            else:
                from_date = None

            self.env[model_name].with_delay().import_batch(
                backend,
                filters={'from_date': from_date, 'to_date': import_start_time}
            )
            # We add a buffer, but won't import them twice.
            next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
            next_time = fields.Datetime.to_string(next_time)
            self.write({from_date_field: next_time})
