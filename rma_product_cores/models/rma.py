# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RMATemplate(models.Model):
    _inherit = 'rma.template'

    usage = fields.Selection(selection_add=[
        ('product_core_sale', 'Product Core Sale'),
        ('product_core_purchase', 'Product Core Purchase'),
    ])

    # Portal Methods
    def _portal_try_create(self, request_user, res_id, **kw):
        if self.usage == 'product_core_sale':
            prefix = 'product_'
            product_map = {int(key[len(prefix):]): float(kw[key]) for key in kw if key.find(prefix) == 0 and kw[key]}
            if product_map:
                service_lines = self._get_product_core_sale_service_lines(request_user.partner_id)
                eligible_service_lines = self._product_core_eligible_service_lines(service_lines)
                eligible_lines = self._rma_product_core_eligible_data(service_lines, eligible_service_lines)
                lines = []
                for product_id, qty in product_map.items():
                    product_f = filter(lambda key_product: key_product.id == product_id, eligible_lines)
                    if product_f:
                        product = next(product_f)
                        product_data = eligible_lines[product]
                        if not qty:
                            continue
                        if qty < 0.0 or product_data['qty_delivered'] < qty:
                            raise ValidationError('Invalid quantity.')
                        lines.append((0, 0, {
                            'product_id': product.id,
                            'product_uom_id': product.uom_id.id,
                            'product_uom_qty': qty,
                        }))
                if not lines:
                    raise ValidationError('Missing product quantity.')
                rma = self.env['rma.rma'].create({
                    'name': _('New'),
                    'template_id': self.id,
                    'partner_id': request_user.partner_id.id,
                    'partner_shipping_id': request_user.partner_id.id,
                    'lines': lines,
                })
                return rma
        return super(RMATemplate, self)._portal_try_create(request_user, res_id, **kw)

    def _portal_template(self, res_id=None):
        if self.usage == 'product_core_sale':
            return 'rma_product_cores.portal_new'
        return super(RMATemplate, self)._portal_template(res_id=res_id)

    def _portal_values(self, request_user, res_id=None):
        if self.usage == 'product_core_sale':
            service_lines = self._get_product_core_sale_service_lines(request_user.partner_id)
            eligible_service_lines = self._product_core_eligible_service_lines(service_lines)
            eligible_lines = self._rma_product_core_eligible_data(service_lines, eligible_service_lines)

            return {
                'rma_template': self,
                'rma_product_core_lines': eligible_lines,
            }
        return super(RMATemplate, self)._portal_values(request_user, res_id=res_id)

    # Product Cores
    def _get_product_core_sale_service_lines(self, partner):
        return partner.sale_order_ids.mapped('order_line').filtered(lambda l: l.core_line_id)\
                                                          .sorted(key=lambda r: r.id)

    def _product_core_eligible_service_lines(self, service_lines, date=None):
        if not date:
            date = fields.Datetime.now()
        lines = service_lines.browse()
        for line in service_lines:
            validity = line.core_line_id.product_id.product_core_validity
            partition_date = date - relativedelta(days=validity)
            if line.order_id.date_order >= partition_date:
                lines += line
        return lines

    def _rma_product_core_eligible_data(self, service_lines, eligible_service_lines):
        rma_model = self.env['rma.rma']
        eligible_lines = defaultdict(lambda: {
            'qty_ordered': 0.0,
            'qty_delivered': 0.0,
            'qty_invoiced': 0.0,
            'lines': self.env['sale.order.line'].browse()})

        for line in service_lines:
            product = rma_model._get_dirty_core_from_service_line(line)
            if product:
                eligible_line = eligible_lines[product]
                eligible_line['lines'] += line
                if line in eligible_service_lines:
                    eligible_line['qty_ordered'] += line.product_uom_qty
                    eligible_line['qty_delivered'] += line.qty_delivered
                    eligible_line['qty_invoiced'] += line.qty_invoiced
        return eligible_lines


class RMA(models.Model):
    _inherit = 'rma.rma'

    def action_done(self):
        res = super(RMA, self).action_done()
        res2 = self._product_core_action_done()
        if isinstance(res, dict) and isinstance(res2, dict):
            if 'warning' in res and 'warning' in res2:
                res['warning'] = '\n'.join([res['warning'], res2['warning']])
                return res
            if 'warning' in res2:
                res['warning'] = res2['warning']
                return res
        elif isinstance(res2, dict):
            return res2
        return res

    def _get_dirty_core_from_service_line(self, line):
        original_product_line = line.core_line_id
        return original_product_line.product_id.product_core_id

    def _product_core_action_done(self):
        for rma in self.filtered(lambda r: r.template_usage in ('product_core_sale', 'product_core_purchase')):
            if rma.template_usage == 'product_core_sale':
                service_lines = rma.template_id._get_product_core_sale_service_lines(rma.partner_id)
                eligible_service_lines = rma.template_id._product_core_eligible_service_lines(service_lines, date=rma.create_date)

                # collect the to reduce qty by product id
                qty_to_reduce = defaultdict(float)
                for line in rma.lines:
                    qty_to_reduce[line.product_id.id] += line.product_uom_qty

                # iterate over all service_lines to see if the qty_delivered can be reduced.
                sale_orders = self.env['sale.order'].browse()
                for line in eligible_service_lines:
                    product = self._get_dirty_core_from_service_line(line)
                    pid = product.id
                    if qty_to_reduce[pid] > 0.0:
                        if line.qty_delivered > 0.0:
                            sale_orders += line.order_id
                            if qty_to_reduce[pid] > line.qty_delivered:
                                # can reduce this whole line
                                qty_to_reduce[pid] -= line.qty_delivered
                                line.write({'qty_delivered': 0.0})
                            else:
                                # can reduce some of this line, but there are no more to reduce
                                line.write({'qty_delivered': line.qty_delivered - qty_to_reduce[pid]})
                                qty_to_reduce[pid] = 0.0

                # if there are more qty to reduce, then we have an error.
                if any(qty_to_reduce.values()):
                    raise UserError(_('Cannot complete RMA as there are not enough service lines to reduce. (Maybe a duplicate)'))

                # Try to invoice if we don't already have an invoice (e.g. from resetting to draft)
                if sale_orders and rma.template_id.invoice_done and not rma.invoice_ids:
                    rma.invoice_ids += rma._product_core_sale_invoice_done(sale_orders)
            else:
                raise UserError(_('not ready for purchase rma'))
        return True

    def _product_core_sale_invoice_done(self, sale_orders):
        return self._sale_invoice_done(sale_orders)

    def action_add_product_core_lines(self):
        make_line_obj = self.env['rma.product_cores.make.lines']
        for rma in self:
            lines = make_line_obj.create({
                'rma_id': rma.id,
            })
            action = self.env.ref('rma_product_cores.action_rma_add_lines').read()[0]
            action['res_id'] = lines.id
            return action

    def _product_cores_create_make_lines(self, wizard, rma_line_model):
        """
        Called from the wizard, as this model "owns" the eligibility and qty on lines.
        :param wizard:
        :param line_model:
        :return:
        """
        if self.partner_id:
            if self.template_usage == 'product_core_sale':
                service_lines = self.template_id._get_product_core_sale_service_lines(self.partner_id)
                eligible_service_lines = self.template_id._product_core_eligible_service_lines(service_lines, date=self.create_date)
                rma_lines = rma_line_model.browse()
                for line in service_lines:
                    product = self._get_dirty_core_from_service_line(line)
                    if product:
                        rma_line = rma_lines.filtered(lambda l: l.product_id == product)
                        if not rma_line:
                            rma_line = rma_line_model.create({
                                'rma_make_lines_id': wizard.id,
                                'product_id': product.id,
                                'product_uom_id': product.uom_id.id,
                            })
                            rma_lines += rma_line
                        if line in eligible_service_lines:
                            rma_line.update({
                                'qty_ordered': rma_line.qty_ordered + line.product_uom_qty,
                                'qty_delivered': rma_line.qty_delivered + line.qty_delivered,
                                'qty_invoiced': rma_line.qty_invoiced + line.qty_invoiced,
                            })
            elif self.template_usage == 'product_core_purchase':
                raise UserError('not ready for purchase rma')

    def _product_core_field_check(self):
        if not self.partner_shipping_id:
            raise UserError(_('You must have a shipping address selected for this RMA.'))
        if not self.partner_id:
            raise UserError(_('You must have a partner selected for this RMA.'))

    def _create_in_picking_product_core_sale(self):
        self._product_core_field_check()
        values = self.template_id._values_for_in_picking(self)
        return self._picking_from_values(values, {}, {})

    def _create_out_picking_product_core_sale(self):
        self._product_core_field_check()
        values = self.template_id._values_for_out_picking(self)
        return self._picking_from_values(values, {}, {})

    def _create_in_picking_product_core_purchase(self):
        self._product_core_field_check()
        values = self.template_id._values_for_in_picking(self)
        return self._picking_from_values(values, {}, {})

    def _create_out_picking_product_core_purchase(self):
        self._product_core_field_check()
        values = self.template_id._values_for_out_picking(self)
        return self._picking_from_values(values, {}, {})
