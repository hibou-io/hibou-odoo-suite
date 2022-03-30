# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import odoo


def migrate(cr, version):
    """
    Update sale_line_id on existing RMA lines to allow completing the RMA
    """
    cr.execute("""
        UPDATE rma_line AS rl
        SET sale_line_id = order_line.id
        FROM (
            SELECT rma_line.id, rma_line.rma_id, rma_line.product_id,
                rank() OVER (PARTITION BY rma_line.rma_id, rma_line.product_id ORDER BY rma_line.id) AS rline
            FROM rma_line
            WHERE rma_line.sale_line_id IS NULL
        ) AS rma_line
        INNER JOIN rma_rma rma 
            ON rma.id = rma_line.rma_id
        INNER JOIN (
            SELECT ol.id, ol.order_id, ol.product_id,
            rank() OVER (PARTITION BY ol.order_id, ol.product_id ORDER BY ol.id) AS oline
            FROM sale_order_line ol
        ) AS order_line
            ON order_line.order_id = rma.sale_order_id
            AND order_line.product_id = rma_line.product_id
            AND order_line.oline = rma_line.rline
        WHERE rma.sale_order_id IS NOT NULL
        AND rma_line.id = rl.id
    """)
