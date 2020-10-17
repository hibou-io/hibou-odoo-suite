from odoo import api, fields, models


class ProgramOutputView(models.TransientModel):
    _name = 'mrp.bom.add'
    _description = 'BoM Add Wizard'

    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials')
    bom_product_tmpl_id = fields.Many2one('product.template', string='BoM Product', related='bom_id.product_tmpl_id')
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    product_variant_count = fields.Integer(string='Variant Count',
                                           compute='_compute_variant_count')
    limit_possible = fields.Boolean(string='Limit to possible variants',
                                    help='Only add variants that can be selected by BoM Product')
    replace_existing = fields.Boolean(string='Replace existing BoM lines for this template.')
    existing_line_count = fields.Integer(string='Existing Lines',
                                         help='Remove any existing lines for this Product Template.',
                                         compute='_compute_variant_count')
    product_qty = fields.Float(string='Quantity to Consume', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Consume Unit of Measure')
    bom_routing_id = fields.Many2one('mrp.routing', related='bom_id.routing_id')
    operation_id = fields.Many2one('mrp.routing.workcenter', 'Consume in Operation')

    @api.depends('product_tmpl_id', 'limit_possible')
    def _compute_variant_count(self):
        self.ensure_one()
        if not self.product_tmpl_id or not self.bom_product_tmpl_id:
            self.product_variant_count = 0
            self.existing_line_count = 0
        else:
            products = self._compute_product_ids()
            lines = self._compute_existing_line_ids()
            self.product_variant_count = len(products)
            self.existing_line_count = len(lines)

    @api.onchange('product_tmpl_id')
    def _onchange_default_product_uom(self):
        if self.product_tmpl_id:
            self.product_uom_id = self.product_tmpl_id.uom_id

    def _compute_attribute_value_ids(self):
        attr_val_ids = self.env['product.attribute.value']
        other_val_ids = self.product_tmpl_id.mapped('attribute_line_ids.value_ids')
        if not self.limit_possible:
            return other_val_ids
        main_product_value_ids = self.bom_product_tmpl_id.mapped('attribute_line_ids.value_ids')
        return main_product_value_ids.filtered(lambda v: v in other_val_ids)

    def _compute_product_ids(self):
        values = self._compute_attribute_value_ids()
        products = self.env['product.product']
        for p in self.product_tmpl_id.product_variant_ids:
            if not p.product_template_attribute_value_ids.mapped('product_attribute_value_id').filtered(lambda a: a not in values):
                # This product's attribute values are in the values set.
                products += p
        return products

    def _compute_existing_line_ids(self):
        return self.bom_id.bom_line_ids.filtered(lambda l: l.product_id.product_tmpl_id == self.product_tmpl_id)

    def add_variants(self):
        if self.replace_existing:
            lines = self._compute_existing_line_ids()
            lines.unlink()

        attribute_values = self._compute_attribute_value_ids()
        products = self._compute_product_ids()
        if not self.product_uom_id:
            self.product_uom_id = self.product_tmpl_id.uom_id
        lines = []
        for p in products:
            bom_product_template_attribute_values = self.bom_product_tmpl_id.attribute_line_ids\
                .mapped('product_template_value_ids')
            p_values = p.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            bom_product_template_attribute_value_ids = bom_product_template_attribute_values \
                .filtered(lambda v: v.product_attribute_value_id in attribute_values and v.product_attribute_value_id in p_values)
            lines.append((0, 0, {
                'bom_id': self.bom_id.id,
                'product_id': p.id,
                'product_qty': self.product_qty,
                'product_uom_id': self.product_uom_id.id,
                'bom_product_template_attribute_value_ids': [(4, a.id, 0)
                                                             for a in bom_product_template_attribute_value_ids],
                'operation_id': self.operation_id.id,
            }))
        self.bom_id.write({'bom_line_ids': lines})
