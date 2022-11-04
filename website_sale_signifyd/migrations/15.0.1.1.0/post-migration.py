# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.


def migrate(cr, version):
    cr.execute('''
        UPDATE signifyd_case
        SET checkpoint_action = 'ACCEPT'
        WHERE guarantee_disposition = 'APPROVED'
    ''')
