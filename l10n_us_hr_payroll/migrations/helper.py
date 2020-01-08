# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

TMP_PREFIX = 'tmp_'

"""
Fields
"""


def field_exists(cr, table_name, field_name):
    cr.execute('SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name=%s and column_name=%s);', (table_name, field_name))
    return cr.fetchone()[0]


def temp_field_exists(cr, table_name, field_name):
    tmp_field_name = TMP_PREFIX + field_name
    cr.execute('SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name=%s and column_name=%s);', (table_name, tmp_field_name))
    return cr.fetchone()[0]


def make_temp_field(cr, table_name, field_name):
    tmp_field_name = TMP_PREFIX + field_name
    cr.execute('SELECT data_type FROM information_schema.columns WHERE table_name=%s and column_name=%s;', (table_name, field_name))
    tmp_field_type = cr.fetchone()[0]
    cr.execute('ALTER TABLE ' + table_name + ' ADD ' + tmp_field_name + ' ' + tmp_field_type)
    cr.execute('UPDATE ' + table_name + ' SET ' + tmp_field_name + '=' + field_name)


def remove_temp_field(cr, table_name, field_name):
    tmp_field_name = TMP_PREFIX + field_name
    cr.execute('ALTER TABLE ' + table_name + ' DROP COLUMN ' + tmp_field_name)


def temp_field_values(cr, table_name, id, field_names):
    tmp_field_names = [TMP_PREFIX + f for f in field_names]
    if not tmp_field_names:
        return {}
    cr.execute('SELECT ' + ', '.join(tmp_field_names) + ' FROM ' + table_name + ' WHERE id=' + str(id))
    values = cr.dictfetchone()
    if not values:
        return {}

    def _remove_tmp_prefix(key):
        if key.startswith(TMP_PREFIX):
            return key[len(TMP_PREFIX):]
        return key
    return {_remove_tmp_prefix(k): v for k, v in values.items()}


"""
XMLIDs
"""


def remove_xmlid(cr, xmlid):
    module, name = xmlid.split('.')
    cr.execute('DELETE FROM ir_model_data WHERE module=%s and name=%s;', (module, name))


def rename_xmlid(cr, from_xmlid, to_xmlid):
    from_module, from_name = from_xmlid.split('.')
    to_module, to_name = to_xmlid.split('.')
    cr.execute('UPDATE ir_model_data SET module=%s, name=%s WHERE module=%s and name=%s;', (to_module, to_name, from_module, from_name))
