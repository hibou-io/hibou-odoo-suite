# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute('''
        ALTER TABLE payment_acquirer
        ADD COLUMN signifyd_case_required BOOLEAN;
    ''')
    cr.execute('''
        UPDATE payment_acquirer
        WHERE signifyd_case_type IS NOT NULL
        SET signifyd_case_required = TRUE;
    ''')
