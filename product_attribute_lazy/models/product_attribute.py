import logging
from datetime import datetime
from odoo import api, fields, models, _, registry, tools
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    
    number_related_products = fields.Integer(compute=False, store=True) # compute='_compute_number_related_products')
    product_tmpl_ids = fields.Many2many('product.template', string="Related Products", compute=False, store=True)  #compute='_compute_products', store=True)

    def action_open_related_products(self):
        self.ensure_one()
        self.env.cr.execute('SELECT product_template_id FROM product_attribute_product_template_rel WHERE product_attribute_id = %s' % (self.id, ))
        tmpl_res = self.env.cr.fetchall()
        tmpl_ids = [t[0] for t in tmpl_res]
        return {
            'type': 'ir.actions.act_window',
            'name': _("Related Products"),
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', tmpl_ids)],
        }

    def _compute_products_sql(self):
        if not self:
            raise UserError('Index with SQL requires attributes.')
        # ORIGINAL for replicating logic
        # for pa in self:
        #     product_tmpls = pa.attribute_line_ids.product_tmpl_id
        #     pa.with_context(active_test=False).product_tmpl_ids = product_tmpls
        #     pa.number_related_products = len(product_tmpls)
        self_ids = ','.join(str(i) for i in self.ids)
        query = """
WITH current_rel AS (
    SELECT 
      attribute_id AS product_attribute_id,
      product_tmpl_id AS product_template_id
    FROM product_template_attribute_line
    WHERE attribute_id in (%s)
    GROUP BY 1, 2
),
expanded_rel AS (
    SELECT
      cr.product_attribute_id as cr_product_attribute_id,
      cr.product_template_id as cr_product_template_id,
      paptr.product_attribute_id as paptr_product_attribute_id,
      paptr.product_template_id as paptr_product_template_id
    FROM current_rel cr
    LEFT JOIN product_attribute_product_template_rel paptr ON paptr.product_attribute_id = cr.product_attribute_id AND paptr.product_template_id = cr.product_template_id
),
not_in_rel AS (
    SELECT
      cr_product_attribute_id as product_attribute_id,
      cr_product_template_id as product_template_id
    FROM expanded_rel
    WHERE paptr_product_attribute_id is null and paptr_product_template_id is null
)

INSERT INTO product_attribute_product_template_rel (product_attribute_id, product_template_id)
SELECT product_attribute_id, product_template_id
FROM not_in_rel;
        """ % (self_ids, )
        query += """
WITH needs_del AS (
          SELECT
            t.product_attribute_id,
            t.product_template_id
          FROM product_attribute_product_template_rel AS t
          LEFT JOIN product_template_attribute_line AS real ON
            real.attribute_id = t.product_attribute_id
            AND real.product_tmpl_id = t.product_template_id
          WHERE t.product_attribute_id in (%s)
            AND real.product_tmpl_id is null
            AND real.attribute_id is null
)
DELETE FROM product_attribute_product_template_rel
WHERE product_attribute_id in (%s) AND (
    (product_attribute_product_template_rel.product_attribute_id,
    product_attribute_product_template_rel.product_template_id) IN (SELECT * FROM needs_del)
);
        """ % (self_ids, self_ids)
        for i in self.ids:
            query += """
UPDATE product_attribute 
SET number_related_products = (SELECT COUNT(*) FROM product_attribute_product_template_rel WHERE product_attribute_id = %s)
WHERE id = %s;
        """ % (i, i)

        self.env.cr.execute(query)

    def _run_indexer(self, use_new_cursor=False):
        indexer_use_sql = self.env['ir.config_parameter'].sudo().get_param('product_attribute_lazy.indexer_use_sql', '1') != '0'
        for pa in self:
            if indexer_use_sql:
                pa._compute_products_sql()
            else:
                pa._compute_products()
            if use_new_cursor:
                pa._cr.commit()
                _logger.info("_run_indexer is finished and committed for %s" % (pa.id, ))

    @api.model
    def run_indexer(self, use_new_cursor=False):
        start_time = datetime.now()
        attributes = None
        try:
            if use_new_cursor:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))

            # We want to freeze the cron that kills long running relationship queries...
            watchdog_cron = self.sudo().env.ref('product_attribute_lazy.ir_cron_product_attribute_rel_query_watchdog', raise_if_not_found=False)
            if watchdog_cron:
                try:
                    with tools.mute_logger('odoo.sql_db'):
                        self._cr.execute("SELECT id FROM ir_cron WHERE id = %s FOR UPDATE NOWAIT", (watchdog_cron.id, ))
                except Exception:
                    _logger.info('Attempt to run indexer aborted, as the query watchdog is already running')
                    self._cr.rollback()
                    raise UserError('Attempt to run indexer aborted, as the query watchdog is already running')

            # if we could tell that it needs re-indexed....
            attributes = self.env['product.attribute'].search([])
            attributes._run_indexer(use_new_cursor=use_new_cursor)
        except Exception:
            _logger.error("Error during product attribute indexer", exc_info=True)
            raise
        finally:
            if use_new_cursor:
                try:
                    self._cr.close()
                except Exception:
                    pass
        if attributes:
            _logger.warning('Indexer took %s seconds total for %s attributes.' % ((datetime.now()-start_time).seconds, len(attributes)))
        return {}

    def run_indexer_manual(self):
        # intended to be called by server action.  Don't allow it to overlap with cron
        if not self.exists():
            raise UserError('One or more selected Product Attributes are required.')
        
        indexer_cron = self.sudo().env.ref('product_attribute_lazy.ir_cron_product_attribute_indexer')
        # Avoid repeated and overlapping index processes
        try:
            with tools.mute_logger('odoo.sql_db'):
                self._cr.execute("SELECT id FROM ir_cron WHERE id = %s FOR UPDATE NOWAIT", (indexer_cron.id, ))
        except Exception:
            _logger.info('Attempt to run indexer aborted, as already running')
            self._cr.rollback()
            raise UserError('Attempt to run indexer aborted, as already running')
        
        self._run_indexer(True)
