# Copyright 2020 Hibou Corp.
# Copyright 2016-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from contextlib import closing

import odoo

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT value FROM ir_config_parameter
        WHERE key = 'ir_attachment.location'
    """)
    row = cr.fetchone()

    if row[0] == 's3':
        uid = odoo.SUPERUSER_ID
        registry = odoo.modules.registry.Registry(cr.dbname)
        new_cr = registry.cursor()
        with closing(new_cr):
            with odoo.api.Environment.manage():
                env = odoo.api.Environment(new_cr, uid, {})
                store_local = env['ir.attachment'].search(
                    [('store_fname', '=like', 's3://%'),
                     '|', ('res_model', '=', 'ir.ui.view'),
                          ('res_field', 'in', ['image_small',
                                               'image_medium',
                                               'web_icon_data',
                                               # image.mixin sizes
                                               # image_128 is essentially image_medium
                                               'image_128',
                                               # depending on use case, these may need migrated/moved
                                               # 'image_256',
                                               # 'image_512',
                                               ])
                     ],
                )

                _logger.info(
                    'Moving %d attachments from S3 to DB for fast access',
                    len(store_local)
                )
                for attachment_id in store_local.ids:
                    # force re-storing the document, will move
                    # it from the object storage to the database

                    # This is a trick to avoid having the 'datas' function
                    # fields computed for every attachment on each
                    # iteration of the loop.  The former issue being that
                    # it reads the content of the file of ALL the
                    # attachments on each loop.
                    try:
                        env.clear()
                        attachment = env['ir.attachment'].browse(attachment_id)
                        _logger.info('Moving attachment %s (id: %s)',
                                     attachment.name, attachment.id)
                        attachment.write({'datas': attachment.datas})
                        new_cr.commit()
                    except:
                        new_cr.rollback()
