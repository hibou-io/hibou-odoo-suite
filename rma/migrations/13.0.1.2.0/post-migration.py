# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

def migrate(cr, installed_version):
    # Provide defaults for RMAs that were created before these fields existed.
    cr.execute('''
UPDATE rma_rma as r
SET initial_in_picking_carrier_id = t.in_carrier_id ,
    initial_out_picking_carrier_id = t.out_carrier_id
FROM rma_template as t
WHERE r.template_id = t.id
    ''')
