# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date


class ProductCoreAgedReport(models.AbstractModel):
    _name = 'product.core.aged.report'
    _description = 'Aged Product Cores'
    _inherit = 'account.report'

    filter_date = {'mode': 'single', 'filter': 'today'}
    filter_unfold_all = False
    filter_partner = True
    order_selected_column = {'default': 0}

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('Partner'), 'class': '', 'style': 'white-space:nowrap;'},
            {'name': _('Date'), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _('Exp. Date'), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _('Account'), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Qty."), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Expired"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Exp. Qty."), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
        ]
        return columns

    def _get_templates(self):
        templates = super(ProductCoreAgedReport, self)._get_templates()
        templates['main_template'] = 'product_cores_report.template_product_core_aged_report'
        templates['line_template'] = 'product_cores_report.template_product_core_aged_line_report'
        return templates

    @api.model
    def _get_lines(self, options, line_id=None):
        # We may need to reverse the sign at some point in the future
        sign = 1.0
        ctx = self._context
        lines = []
        cr = self.env.cr
        user_company = self.env.company
        company_ids = self._context.get('company_ids') or [user_company.id]

        # expand line, filter just for this product
        product = False
        if line_id and 'product_' in line_id:
            # we only want to fetch data about this product because we are expanding a line
            product_id_str = line_id.split('_')[1]
            if product_id_str.isnumeric():
                product = self.env['product.product'].browse(int(product_id_str))

        date_from = fields.Date.from_string(self._context['date_to'])

        # put in to constants CTE for easier query
        arg_list = (date_from, )

        # product filtering
        product_clause = ''
        if product:
            product_clause = 'AND (pp.id IN %s)'
            arg_list += (tuple(product.ids), )

        # partner filtering
        partner_clause = ''
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)

        query = '''
            WITH 
            constants (date_from) AS (VALUES (%s)), 
            product_cores AS (
                SELECT pp.id AS id, pt.product_core_validity AS product_core_validity, pt.name AS product_name
                FROM product_template AS pt
                INNER JOIN product_product AS pp ON pp.product_tmpl_id = pt.id
                WHERE pt.core_ok = true
                    AND pt.type = 'service'
                ''' + product_clause + '''
            )
            SELECT pc.id AS product_id,
                MAX(pc.product_name) AS product_name,
                MAX(UPPER(pc.product_name)) AS UPNAME,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) < (SELECT date_from FROM constants) AND l.debit != 0 THEN ABS(l.quantity)
                      WHEN COALESCE(l.date_maturity, l.date) < (SELECT date_from FROM constants) THEN -ABS(l.quantity)
                      ELSE 0.0 END) AS total_expired_qty,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) < (SELECT date_from FROM constants) THEN l.debit
                      ELSE 0.0 END) AS total_expired_debit,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) < (SELECT date_from FROM constants) THEN l.credit
                      ELSE 0.0 END) AS total_expired_credit,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants) AND l.debit != 0 THEN ABS(l.quantity)
                      WHEN COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants) THEN -ABS(l.quantity)
                      ELSE 0.0 END) AS total_qty,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants) THEN l.debit
                      ELSE 0.0 END) AS total_debit,
                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants) THEN l.credit
                      ELSE 0.0 END) AS total_credit,
                                SUM(CASE 
                      WHEN COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants) THEN l.credit
                      ELSE 0.0 END) AS total_credit,
                array_agg(l.id) FILTER (WHERE COALESCE(l.date_maturity, l.date) >= (SELECT date_from FROM constants)) AS aml_ids
            FROM account_move_line AS l
              INNER JOIN product_cores AS pc ON l.product_id = pc.id
            WHERE (l.date <= (SELECT date_from FROM constants))
                ''' + partner_clause + '''
                AND (l.company_id IN %s)
                GROUP BY pc.id
                ORDER BY UPNAME ASC
                '''
        arg_list += (tuple(company_ids), )
        cr.execute(query, arg_list)

        totals = {'total': 0.0, 'total_qty': 0.0, 'total_expired': 0.0, 'total_expired_qty': 0.0}
        product_cores = cr.dictfetchall()
        for product_core in product_cores:
            ref = 'product_%s' % (product_core['product_id'], )
            product_total = product_core['total_debit'] - product_core['total_credit']
            product_total_qty = product_core['total_qty']
            product_expired_total = product_core['total_expired_debit'] - product_core['total_expired_credit']
            product_expired_total_qty = product_core['total_expired_qty']
            totals['total'] += product_total
            totals['total_qty'] += product_total_qty
            totals['total_expired'] += product_expired_total
            totals['total_expired_qty'] += product_expired_total_qty
            vals = {
                'id': ref,
                'name': product_core['product_name'],
                'level': 2,
                'columns': [{'name': ''}] * 4 +
                           [{'name': self.format_value(sign * product_total), 'no_format': sign * product_total},
                            {'name': sign * product_total_qty, 'no_format': sign * product_total_qty},
                            {'name': self.format_value(sign * product_expired_total), 'no_format': sign * product_expired_total},
                            {'name': sign * product_expired_total_qty, 'no_format': sign * product_expired_total_qty},
                            ],
                'unfoldable': True,
                'unfolded': ref in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if ref in options.get('unfolded_lines'):
                amls = self.env['account.move.line'].browse(product_core['aml_ids'])
                for aml in amls:
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    expires = aml.date_maturity if aml.date_maturity else aml.date
                    expired = expires < date_from
                    amount = aml.debit - aml.credit
                    amount_not_expired = amount if not expired else 0.0
                    amount_expired = amount if expired else 0.0
                    qty = abs(aml.quantity) if aml.debit else -abs(aml.quantity)
                    qty_not_expired = qty if not expired else 0.0
                    qty_expired = qty if expired else 0.0

                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': ref,
                        'columns': [{'name': v} for v in [aml.partner_id.display_name or 'Undefined', format_date(self.env, aml.date), format_date(self.env, expires), aml.account_id.display_name]] +
                                   [{'name': self.format_value(sign * amount_not_expired, blank_if_zero=True), 'no_format': sign * amount_not_expired},
                                    {'name': sign * qty_not_expired or '', 'no_format': sign * qty_not_expired},
                                    {'name': self.format_value(sign * amount_expired, blank_if_zero=True), 'no_format': sign * amount_expired},
                                    {'name': sign * qty_expired or '', 'no_format': sign * qty_expired},
                                    ],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, aml.ref, aml.move_id.name),
                    }
                    lines.append(vals)

        if not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 4 +
                           [{'name': self.format_value(sign * totals['total']), 'no_format': sign * totals['total']},
                            {'name': sign * totals['total_qty'], 'no_format': sign * totals['total_qty']},
                            {'name': self.format_value(sign * totals['total_expired']), 'no_format': sign * totals['total_expired']},
                            {'name': sign * totals['total_expired_qty'], 'no_format': sign * totals['total_expired_qty']},
                            ],
            }
            lines.append(total_line)

        return lines
