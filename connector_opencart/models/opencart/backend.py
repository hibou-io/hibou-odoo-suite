# © 2019 Hibou Corp.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from logging import getLogger
from contextlib import contextmanager

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.connector.models.checkpoint import add_checkpoint
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
    # payment_mode_id = fields.Many2one(comodel_name='account.payment.mode', string="Payment Mode")
    coupon_product_id = fields.Many2one(comodel_name='product.product', string='Coupon Product',
                                        help='Product to represent coupon discounts.')

    # New Product fields.
    product_categ_id = fields.Many2one(comodel_name='product.category', string='Product Category',
                                       help='Default product category for newly created products.')

    import_orders_after_id = fields.Integer(
        string='Import sale orders after id',
    )

    so_require_product_setup = fields.Boolean(string='SO Require Product Setup',
                                              help='Prevents SO from being confirmed (failed queue job), if one or more products has an open checkpoint.')

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        opencart_api = Opencart(self.base_url, self.restadmin_token)
        _super = super(OpencartBackend, self)
        with _super.work_on(model_name, opencart_api=opencart_api, **kwargs) as work:
            yield work

    @api.multi
    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return add_checkpoint(self.env, record._name, record.id,
                              self._name, self.id)

    @api.multi
    def find_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        checkpoint_model = self.env['connector.checkpoint']
        model_model = self.env['ir.model']
        model = model_model.search([('model', '=', record._name)], limit=1)
        return checkpoint_model.search([
            ('backend_id', '=', '%s,%s' % (self._name, self.id)),
            ('model_id', '=', model.id),
            ('record_id', '=', record.id),
            ('state', '=', 'need_review'),
        ], limit=1)

    @api.multi
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
            ('import_orders_after_id', '!=', False),
        ])
        return backends.import_sale_orders()

    @api.multi
    def import_sale_orders(self):
        self._import_after_id('opencart.sale.order', 'import_orders_after_id')
        return True

    @api.multi
    def _import_after_id(self, model_name, after_id_field):
        for backend in self:
            after_id = backend[after_id_field]
            self.env[model_name].with_delay().import_batch(
                backend,
                filters={'after_id': after_id}
            )
            # TODO !!!!!
            # cannot update the ID because we don't know what Ids would be returned.
            # this MUST be updated by the SO importer.
