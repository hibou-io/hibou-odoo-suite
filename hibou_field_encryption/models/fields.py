import json
import logging
import os
import struct

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken, MultiFernet
except ImportError as err:  # pragma: no cover
    _logger.debug(err)
    Fernet = None
    MultiFernet = None

try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions
except ImportError as err:  # pragma: no cover
    _logger.debug(err)
    secretmanager = None
    gcp_exceptions = None

REC_ENCRYPTION_KEY = "rec_encryption_key"
REC_ENCRYPTION_KEY_PROVIDER = "rec_encryption_key_provider"
GCP_SECRET_NAME = "rec_encryption_gcp_secret"
GCP_PROJECT = "rec_encryption_gcp_project"
DEFAULT_ENCRYPTION_FIELD = "rec_encrypted"

# Wire-format: encrypted blobs are prefixed with a 3-byte header
#   byte 0   : format version (0x01)
#   byte 1-2 : big-endian uint16 key version
# Blobs that do NOT start with 0x01 are assumed to be legacy (pre-keyring)
# data encrypted with key version 0.
_HEADER_FORMAT = 0x01
_HEADER_STRUCT = struct.Struct('>BH')  # 3 bytes: uint8 + uint16


def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate


# ---------------------------------------------------------------------------
# Keyring – ordered collection of versioned Fernet keys
# ---------------------------------------------------------------------------

class EncryptionKeyring:
    """Holds a set of versioned Fernet keys.

    *keys* is an ordered mapping ``{version_int: Fernet}`` where the
    **last** entry is the current (encryption) key and earlier entries
    are retained only for decryption of old data.

    The single-key legacy configuration (one ``REC_ENCRYPTION_KEY``) is
    represented as ``{0: Fernet(key)}``.
    """

    def __init__(self, keys=None):
        self._keys = dict(keys or {})

    @property
    def current_version(self):
        if not self._keys:
            raise ValidationError(_("Encryption keyring is empty."))
        return max(self._keys)

    @property
    def current_fernet(self):
        return self._keys[self.current_version]

    def fernet_for_version(self, version):
        f = self._keys.get(version)
        if f is None:
            raise ValidationError(
                    "No key found for version %(ver)s. The data may have been "
                    "encrypted with a key that has been revoked.",
                    ver=version,
            )
        return f

    @property
    def versions(self):
        return sorted(self._keys)

    def __len__(self):
        return len(self._keys)

    def __contains__(self, version):
        return version in self._keys


_keyring_instance = None


# ---------------------------------------------------------------------------
# Key providers
# ---------------------------------------------------------------------------

def _load_keyring_from_config():
    """Build a keyring from the ``rec_encryption_key`` config/env value.

    Supports two shapes:

    **Single key** (backward compatible)::

        rec_encryption_key = <base64-fernet-key>

    **Multi-key keyring** (for rotation)::

        rec_encryption_key = 0:<key0>,1:<key1>,2:<key2>
    """
    key_str = config.get(REC_ENCRYPTION_KEY) or os.environ.get(REC_ENCRYPTION_KEY.upper())
    if not key_str:
        raise ValidationError(
            # TODO FIX cannot use translated here!
''
        )

    key_str = key_str.strip()
    keys = {}

    if ':' in key_str and ',' in key_str:
        for part in key_str.split(','):
            part = part.strip()
            if not part:
                continue
            ver_str, _, k = part.partition(':')
            try:
                ver = int(ver_str)
            except ValueError:
                raise ValidationError(
                    _(
                        "Invalid key version '%(ver)s' in keyring configuration.",
                        ver=ver_str,
                    )
                )
            keys[ver] = Fernet(k.strip().encode())
    else:
        keys[0] = Fernet(key_str.encode())

    return EncryptionKeyring(keys)


def _load_keyring_from_gcp():
    """Build a keyring from a Google Cloud Secret Manager secret.

    Each **enabled** version of the GCP secret becomes a key in the
    keyring.  The GCP version number maps directly to the keyring
    version.  The version payload must be a raw Fernet key (base64).

    Required configuration (config file or env):

    - ``rec_encryption_gcp_project`` / ``REC_ENCRYPTION_GCP_PROJECT``
    - ``rec_encryption_gcp_secret``  / ``REC_ENCRYPTION_GCP_SECRET``
    """
    if secretmanager is None:
        raise UserError(
            _(
                "The library 'google-cloud-secret-manager' is missing. "
                "Install it with: pip install google-cloud-secret-manager"
            )
        )

    project = config.get(GCP_PROJECT) or os.environ.get(GCP_PROJECT.upper())
    if not project:
        raise ValidationError(
            _(
                "GCP key provider requires '%(key)s' in the config file or "
                "%(env)s environment variable.",
                key=GCP_PROJECT,
                env=GCP_PROJECT.upper(),
            )
        )

    secret_id = config.get(GCP_SECRET_NAME) or os.environ.get(GCP_SECRET_NAME.upper())
    if not secret_id:
        raise ValidationError(
            _(
                "GCP key provider requires '%(key)s' in the config file or "
                "%(env)s environment variable.",
                key=GCP_SECRET_NAME,
                env=GCP_SECRET_NAME.upper(),
            )
        )

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project}/secrets/{secret_id}"

    versions = client.list_secret_versions(
        request={"parent": parent, "filter": "state:ENABLED"}
    )

    keys = {}
    for v in versions:
        ver_num = int(v.name.rsplit("/", 1)[-1])
        response = client.access_secret_version(request={"name": v.name})
        key_bytes = response.payload.data.strip()
        try:
            keys[ver_num] = Fernet(key_bytes)
        except Exception:
            _logger.warning(
                "GCP secret version %s is not a valid Fernet key, skipping.",
                v.name,
            )

    if not keys:
        raise ValidationError(
            _(
                "No valid Fernet keys found in GCP secret '%(secret)s' "
                "(project '%(project)s').",
                secret=secret_id,
                project=project,
            )
        )

    _logger.info(
        "Loaded encryption keyring from GCP Secret Manager: "
        "%d key(s), current version %d.",
        len(keys), max(keys),
    )
    return EncryptionKeyring(keys)


_KEY_PROVIDERS = {
    "config": _load_keyring_from_config,
    "gcp_secret_manager": _load_keyring_from_gcp,
}


def _load_keyring():
    if Fernet is None:
        raise UserError(_("The library 'cryptography' is missing, Fernet import cannot proceed."))

    provider_name = (
        config.get(REC_ENCRYPTION_KEY_PROVIDER)
        or os.environ.get(REC_ENCRYPTION_KEY_PROVIDER.upper(), "config")
    )
    provider_fn = _KEY_PROVIDERS.get(provider_name)
    if provider_fn is None:
        raise ValidationError(
            _(
                "Unknown encryption key provider '%(name)s'. "
                "Available: %(avail)s",
                name=provider_name,
                avail=", ".join(sorted(_KEY_PROVIDERS)),
            )
        )
    return provider_fn()


def get_keyring():
    global _keyring_instance
    if _keyring_instance is None:
        _keyring_instance = _load_keyring()
    return _keyring_instance


def reset_keyring():
    global _keyring_instance
    _keyring_instance = None


# ---------------------------------------------------------------------------
# Wire-format helpers
# ---------------------------------------------------------------------------

def _pack_header(key_version):
    return _HEADER_STRUCT.pack(_HEADER_FORMAT, key_version)


def _unpack_header(blob):
    """Return ``(key_version, ciphertext)`` from a stored blob.

    If the blob does not carry our header (legacy data) return
    ``(0, blob)`` so it will be decrypted with key version 0.
    """
    if len(blob) >= _HEADER_STRUCT.size:
        fmt, ver = _HEADER_STRUCT.unpack_from(blob)
        if fmt == _HEADER_FORMAT:
            return ver, blob[_HEADER_STRUCT.size:]
    return 0, blob


# ---------------------------------------------------------------------------
# Implement encrypt fields by monkey-patching fields.Field
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Definition and implementation of encryption fields
# ---------------------------------------------------------------------------

class Encryption(fields.Field):
    """ Encryption fields provide the storage for encrypt fields. """
    type = 'encryption'
    column_type = ('bytea', 'bytea')

    prefetch = False                    # not prefetched by default

    def _get_cipher(self):
        """Return the *current* Fernet cipher (for backward compat).

        Prefer :func:`get_keyring` for new code.
        """
        return get_keyring().current_fernet

    def _encrypt_data(self, data):
        if not isinstance(data, bytes):
            data = data.encode()
        keyring = get_keyring()
        version = keyring.current_version
        ciphertext = keyring.current_fernet.encrypt(data or b'{}')
        return _pack_header(version) + ciphertext

    def _decrypt_data(self, value):
        if not value:
            return '{}'
        if isinstance(value, memoryview):
            value = bytes(value)
        version, ciphertext = _unpack_header(value)
        keyring = get_keyring()
        try:
            fernet = keyring.fernet_for_version(version)
            return fernet.decrypt(ciphertext).decode()
        except ValidationError:
            _logger.error(
                "%s was encrypted with revoked key version %s. "
                "The data is unreadable.",
                self.name, version,
            )
            return '{}'
        except InvalidToken:
            _logger.error(
                "%s has been encrypted with a different key "
                "(version %s). Unless you can recover the previous key, "
                "this %s is unreadable.",
                self.name, version, self.name,
            )
            return '{}'

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

# Monkey-patch _setup_base to inject Encryption fields into _fields.
# In Odoo, _setup_base collects class-attribute fields into _fields.
# Fields dynamically created via encrypt=True in _get_attrs would be
# too late, so we inject them at the end of _setup_base instead.
_original_setup_base = models.BaseModel._setup_base

def _inject_encryption_field(model, enc_name):
    enc_field = Encryption(string='Encrypted Data')
    enc_field.args = {'string': 'Encrypted Data'}
    enc_field.name = enc_name
    enc_field.string = 'Encrypted Data'
    enc_field.model_name = model._name
    enc_field._modules = {'hibou_field_encryption'}
    model._fields[enc_name] = enc_field
    # Also set on the model's class so _add_inherited_fields
    # on _inherits children passes the hasattr check in _add_field.
    try:
        type.__setattr__(type(model), enc_name, enc_field)
    except (TypeError, AttributeError):
        pass


def _collect_enc_names_from_fields(fields_dict):
    enc_names = set()
    for field in fields_dict.values():
        enc = getattr(field, 'encrypt', None) or (getattr(field, 'args', None) or {}).get('encrypt')
        if enc:
            enc_names.add(DEFAULT_ENCRYPTION_FIELD if enc is True else enc)
    return enc_names


def _patched_setup_base(self):
    # Inject encryption storage fields on self before _original_setup_base
    # so they are available during _add_inherited_fields.
    for enc_name in _collect_enc_names_from_fields(self._fields):
        if enc_name not in self._fields:
            _inject_encryption_field(self, enc_name)
    # Also inject on _inherits parents — their encrypt fields may
    # reference storage fields that haven't been created yet.
    pool = getattr(self, 'pool', None)
    if pool:
        for parent_model_name in getattr(self, '_inherits', {}):
            parent = pool.get(parent_model_name)
            if parent is None:
                continue
            for enc_name in _collect_enc_names_from_fields(parent._fields):
                if enc_name not in parent._fields:
                    _inject_encryption_field(parent, enc_name)
    _original_setup_base(self)
    enc_names = set()
    for field in self._fields.values():
        enc = getattr(field, 'encrypt', None)
        if enc:
            enc_names.add(DEFAULT_ENCRYPTION_FIELD if enc is True else enc)
    for enc_name in enc_names:
        if enc_name not in self._fields:
            _inject_encryption_field(self, enc_name)

models.BaseModel._setup_base = _patched_setup_base


# ---------------------------------------------------------------------------
# Re-encryption helper
# ---------------------------------------------------------------------------

def re_encrypt_blob(blob):
    """Decrypt *blob* with whatever key version it carries and
    re-encrypt with the **current** key.

    Returns ``(changed, new_blob)`` where *changed* is ``True`` when
    the blob was actually re-encrypted (i.e. it was not already using
    the current key version).
    """
    if not blob:
        return False, blob
    if isinstance(blob, memoryview):
        blob = bytes(blob)
    version, ciphertext = _unpack_header(blob)
    keyring = get_keyring()
    if version == keyring.current_version:
        return False, blob
    fernet = keyring.fernet_for_version(version)
    plaintext = fernet.decrypt(ciphertext)
    new_ciphertext = keyring.current_fernet.encrypt(plaintext)
    return True, _pack_header(keyring.current_version) + new_ciphertext


def re_encrypt_table(cr, table, encryption_field=None):
    """Re-encrypt every row in *table* to the current key version.

    Returns the number of rows that were actually updated.
    """
    encryption_field = encryption_field or DEFAULT_ENCRYPTION_FIELD
    cr.execute(
        'SELECT id, "{}" FROM "{}" WHERE "{}" IS NOT NULL'.format(
            encryption_field, table, encryption_field,
        )
    )
    updated = 0
    for rec_id, raw in cr.fetchall():
        raw = bytes(raw) if isinstance(raw, memoryview) else raw
        changed, new_blob = re_encrypt_blob(raw)
        if changed:
            cr.execute(
                'UPDATE "{}" SET "{}" = %s WHERE id = %s'.format(
                    table, encryption_field,
                ),
                (new_blob, rec_id),
            )
            updated += 1
    return updated


# ---------------------------------------------------------------------------
# Migration helper (unchanged public API)
# ---------------------------------------------------------------------------

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
