from odoo.tests.common import TransactionCase


class TestMRPBOMAdd(TransactionCase):

    def setUp(self):
        super(TestMRPBOMAdd, self).setUp()
        self.attr1 = self.env['product.attribute'].create({
            'name': 'Test Attr1',
            'create_variant': 'always',
            'type': 'radio',
        })
        self.attr1_val1 = self.env['product.attribute.value'].create({
            'attribute_id': self.attr1.id,
            'name': 'Test Attr1 Val1'
        })
        self.attr1_val2 = self.env['product.attribute.value'].create({
            'attribute_id': self.attr1.id,
            'name': 'Test Attr2 Val1'
        })

        self.attr2 = self.env['product.attribute'].create({
            'name': 'Test Attr2',
            'create_variant': 'always',
            'type': 'radio',
        })
        self.attr2_val1 = self.env['product.attribute.value'].create({
            'attribute_id': self.attr2.id,
            'name': 'Test Attr2 Val1'
        })
        self.attr2_val2 = self.env['product.attribute.value'].create({
            'attribute_id': self.attr2.id,
            'name': 'Test Attr2 Val2'
        })

        # 2 variant product
        self.manufacture = self.env['product.template'].create({
            'name': 'Test Manufactured',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr1.id,
                    'value_ids': [(4, self.attr1_val1.id, 0)],
                }),
                (0, 0, {
                    'attribute_id': self.attr2.id,
                    'value_ids': [(4, self.attr2_val1.id, 0), (4, self.attr2_val2.id, 0)],
                }),
            ]
        })

        # 4 variant component
        self.component = self.env['product.template'].create({
            'name': 'Test Component',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr1.id,
                    'value_ids': [(4, self.attr1_val1.id, 0), (4, self.attr1_val2.id, 0)],
                }),
                (0, 0, {
                    'attribute_id': self.attr2.id,
                    'value_ids': [(4, self.attr2_val1.id, 0), (4, self.attr2_val2.id, 0)],
                }),
            ]
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.manufacture.id,
            'product_qty': 1.0,
            'product_uom_id': self.manufacture.uom_id.id,
        })

    def test_internals(self):
        # Ensure BoM is empty
        self.assertEqual(len(self.bom.bom_line_ids), 0)
        wizard = self.env['mrp.bom.add'].create({
            'bom_id': self.bom.id,
        })
        wizard.product_tmpl_id = self.component
        self.assertEqual(wizard._compute_attribute_value_ids(),
                         self.component.mapped('attribute_line_ids.value_ids'))
        self.assertEqual(wizard._compute_product_ids(), self.component.product_variant_ids)
        wizard.limit_possible = True
        self.assertEqual(wizard._compute_attribute_value_ids(),
                         self.manufacture.mapped('attribute_line_ids.value_ids'))

    def test_main(self):
        # Ensure BoM is empty
        self.assertEqual(len(self.bom.bom_line_ids), 0)

        wizard = self.env['mrp.bom.add'].create({
            'bom_id': self.bom.id,
        })
        self.assertEqual(wizard.product_variant_count, 0)

        wizard.product_tmpl_id = self.component
        self.assertEqual(wizard.product_variant_count, 4)

        wizard.add_variants()
        self.assertEqual(len(self.bom.bom_line_ids), 4)

    def test_limited(self):
        # Ensure BoM is empty
        self.assertEqual(len(self.bom.bom_line_ids), 0)

        wizard = self.env['mrp.bom.add'].create({
            'bom_id': self.bom.id,
        })
        self.assertEqual(wizard.product_variant_count, 0)

        wizard.limit_possible = True
        wizard.product_tmpl_id = self.component
        self.assertEqual(wizard.product_variant_count, 2)

        wizard.add_variants()
        self.assertEqual(len(self.bom.bom_line_ids), 2)

    def test_replace(self):
        # Ensure BoM is empty
        self.assertEqual(len(self.bom.bom_line_ids), 0)

        wizard = self.env['mrp.bom.add'].create({
            'bom_id': self.bom.id,
        })

        wizard.product_tmpl_id = self.component
        self.assertEqual(wizard.product_variant_count, 4)

        wizard.add_variants()
        self.assertEqual(len(self.bom.bom_line_ids), 4)

        # Additive
        wizard.add_variants()
        self.assertEqual(len(self.bom.bom_line_ids), 8)

        # remove those 8 lines when adding new ones
        wizard.replace_existing = True
        wizard.add_variants()
        self.assertEqual(len(self.bom.bom_line_ids), 4)
