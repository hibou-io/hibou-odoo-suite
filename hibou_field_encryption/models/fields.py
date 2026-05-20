import json
import logging
import os

from odoo import fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as err:  # pragma: no cover
    _logger.debug(err)
    Fernet = None

REC_ENCRYPTION_KEY = "rec_encryption_key"
DEFAULT_ENCRYPTION_FIELD = "rec_encrypted"

def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate


#
# Implement encrypt fields by monkey-patching fields.Field
#

fields.Field.__doc__ += """

        .. _field-encrypt:

        .. rubric:: Encrypt fields

        :param encrypt: the name of the field where the value of this field must be stored.
"""
fields.Field.encrypt = None

@monkey_patch(fields.Field)
def _get_attrs(self, model_class, name):
    attrs = _get_attrs.super(self, model_class, name)
    if attrs.get('encrypt'):
        if attrs['encrypt'] is True:
            attrs['encrypt'] = DEFAULT_ENCRYPTION_FIELD
        if not hasattr(model_class, attrs['encrypt']):
            setattr(model_class, attrs['encrypt'], Encryption())
        # by default, encrypt fields are not stored and not copied
        attrs['store'] = False
        attrs['copy'] = attrs.get('copy', False)
        attrs['compute'] = self._compute_encrypt
        if not attrs.get('readonly'):
            attrs['inverse'] = self._inverse_encrypt
    return attrs

@monkey_patch(fields.Field)
def _compute_encrypt(self, records):
    for record in records:
        values = record[self.encrypt]
        record[self.name] = values.get(self.name)
    if self.relational:
        for record in records:
            record[self.name] = record[self.name].exists()

@monkey_patch(fields.Field)
def _inverse_encrypt(self, records):
    for record in records:
        values = record[self.encrypt]
        value = self.convert_to_read(record[self.name], record)
        if value:
            if values.get(self.name) != value:
                values[self.name] = value
                record[self.encrypt] = values
        else:
            if self.name in values:
                values.pop(self.name)
                record[self.encrypt] = values


#
# Definition and implementation of encryption fields
#

class Encryption(fields.Field):
    """ Encryption fields provide the storage for encrypt fields. """
    type = 'encryption'
    column_type = ('bytea', 'bytea')

    prefetch = False                    # not prefetched by default

    def _get_cipher(self):
        """Return a cipher using the key from the Odoo config file
        or the REC_ENCRYPTION_KEY environment variable.
        """
        if Fernet is None:
            raise UserError(_("The library 'cryptography' is missing, Fernet import cannot proceed."))

        key_str = config.get(REC_ENCRYPTION_KEY) or os.environ.get(REC_ENCRYPTION_KEY.upper())
        if not key_str:
            raise ValidationError(
                _(
                    "No '%(key_name)s' entry found in config file or "
                    "%(env_var)s environment variable. "
                    "Use a key similar to: %(key)s",
                    key_name=REC_ENCRYPTION_KEY,
                    env_var=REC_ENCRYPTION_KEY.upper(),
                    key=Fernet.generate_key().decode(),
                )
            )
        # key should be in bytes format
        key = key_str.encode()
        return Fernet(key)

    def _encrypt_data(self, data):
        if not isinstance(data, bytes):
            data = data.encode()
        return self._get_cipher().encrypt(data or b'{}')

    def _decrypt_data(self, value):
        cipher = self._get_cipher()
        try:
            return cipher.decrypt(value).decode()
        except InvalidToken as exc:
            _logger.error(
                f"{self.name} has been encrypted with a different "
                "key. Unless you can recover the previous key, "
                f"this {self.name} is unreadable."
            )
            return {}

    def convert_to_column_insert(self, value, record, values=None, validate=True):
        return self.convert_to_cache(value, record, validate=validate)

    def convert_to_cache(self, value, record, validate=True):
        value = value or {}
        # cache format: json.dumps(value) or None
        return self._encrypt_data(json.dumps(value)) if isinstance(value, dict) else (value or None)

    def convert_to_record(self, value, record):
        if isinstance(value, memoryview):
            value = bytes(value)
        if isinstance(value, str):
            # the cache must contain bytes or memoryview, but sometimes a string
            # is given when assigning a binary field (test `TestFileSeparator`)
            value = value.encode()
        return json.loads(self._decrypt_data(value)) if value else {}

fields.Encryption = Encryption


def migrate_fields_to_encryption(cr, table, field_names, encryption_field=None, drop_columns=False):
    """Migrate plaintext DB columns into an Encryption blob.

    Call from a post-migration script or post_init_hook.

    :param cr: database cursor
    :param table: SQL table name (e.g. 'res_partner')
    :param field_names: list of column names to migrate (e.g. ['secret_note', 'ssn'])
    :param encryption_field: name of the Encryption column (default: DEFAULT_ENCRYPTION_FIELD)
    :param drop_columns: if True, DROP the old plaintext columns after migration
    """
    encryption_field = encryption_field or DEFAULT_ENCRYPTION_FIELD
    enc = Encryption()

    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name = ANY(%s)
    """, (table, list(field_names)))
    existing_columns = [r[0] for r in cr.fetchall()]
    if not existing_columns:
        return

    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, encryption_field))
    if not cr.fetchone():
        cr.execute('ALTER TABLE "{}" ADD COLUMN "{}" bytea'.format(table, encryption_field))

    where = ' OR '.join('"{}" IS NOT NULL'.format(col) for col in existing_columns)
    cols_sql = ', '.join('"{}"'.format(col) for col in existing_columns)
    cr.execute('SELECT id, "{}", {} FROM "{}" WHERE {}'.format(
        encryption_field, cols_sql, table, where))

    for row in cr.fetchall():
        rec_id = row[0]
        existing_blob = row[1]
        if existing_blob:
            existing_blob = bytes(existing_blob) if isinstance(existing_blob, memoryview) else existing_blob
            data = json.loads(enc._decrypt_data(existing_blob))
        else:
            data = {}
        for i, col in enumerate(existing_columns):
            val = row[2 + i]
            if val is not None:
                data[col] = val
        encrypted = enc._encrypt_data(json.dumps(data))
        cr.execute('UPDATE "{}" SET "{}" = %s WHERE id = %s'.format(
            table, encryption_field), (encrypted, rec_id))

    if drop_columns:
        for col in existing_columns:
            cr.execute('ALTER TABLE "{}" DROP COLUMN IF EXISTS "{}"'.format(table, col))
