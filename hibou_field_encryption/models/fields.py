import json
import logging
import os
import struct
import time

from odoo import fields, models
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
REC_ENCRYPTION_KEY_PATH = "rec_encryption_key_path"
REC_ENCRYPTION_KEY_PROVIDER = "rec_encryption_key_provider"
REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT = "rec_encryption_disable_auto_reencrypt"
GCP_SECRET_NAME = "rec_encryption_gcp_secret"
GCP_PROJECT = "rec_encryption_gcp_project"
DEFAULT_ENCRYPTION_FIELD = "rec_encrypted"

DEFAULT_REENCRYPT_BATCH_SIZE = 1000
_TRUTHY = ('1', 'true', 'yes', 'on', 'enabled')

# Providers whose key set can change while Odoo is running. Only these are
# worth polling; a config value cannot change under a live process.
EXTERNALLY_MANAGED_PROVIDERS = ("gcp_secret_manager", "file")

# Wire-format: encrypted blobs are prefixed with a 3-byte header
#   byte 0   : format version (0x01)
#   byte 1-2 : big-endian uint16 key version
# Blobs that do NOT start with 0x01 are assumed to be legacy (pre-keyring)
# data encrypted with key version 0.
_HEADER_FORMAT = 0x01
_HEADER_STRUCT = struct.Struct('>BH')  # 3 bytes: uint8 + uint16


class DecryptFailed(Exception):
    """A stored blob exists but could not be decrypted with the current keyring.

    Raised rather than returning empty data, because the two are not
    interchangeable: an empty blob means "nothing was stored", while a blob we
    cannot read means "something was stored and we must not overwrite it".
    """

    def __init__(self, message, key_version=None):
        super().__init__(message)
        self.key_version = key_version


class UndecryptableData(dict):
    """Placeholder for a blob that could not be decrypted.

    Reads degrade to empty, as they always have. Writes do not: re-encrypting
    this would persist an empty dict over fields that were merely unreadable,
    destroying them for good even if the key is recovered later. Callers that
    write check for this type and refuse.
    """

    __slots__ = ()


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
            raise ValidationError("Encryption keyring is empty.")
        return max(self._keys)

    @property
    def current_fernet(self):
        return self._keys[self.current_version]

    def fernet_for_version(self, version):
        f = self._keys.get(version)
        if f is None:
            raise ValidationError(
                "No key found for version %s. The data may have been "
                "encrypted with a key that has been revoked." % version
            )
        return f

    @property
    def versions(self):
        return sorted(self._keys)

    def __len__(self):
        return len(self._keys)

    def __contains__(self, version):
        return version in self._keys


# Process-global, deliberately not per-database. Every database served by this
# process shares one keyring, because the key source is process configuration.
# That suits one-database-per-process deployments; a multi-tenant process
# serving databases with different keys is not supported, and reset_keyring()
# from one database's registry load affects all of them.
_keyring_instance = None


# ---------------------------------------------------------------------------
# Key providers
# ---------------------------------------------------------------------------

def _get_setting(name, default=None):
    """Read *name* from the Odoo config, falling back to the upper-cased
    environment variable.
    """
    value = config.get(name)
    if value in (None, ''):
        value = os.environ.get(name.upper())
    if value in (None, ''):
        return default
    return value


def auto_reencrypt_disabled():
    """True when automatic re-encryption must not run.

    Automatic re-encryption is **on by default**: whenever the keyring holds
    more than one key version, old blobs are rewritten to the current version
    at startup. Set ``rec_encryption_disable_auto_reencrypt`` (config) or
    ``REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT`` (env) to opt out and rotate
    manually instead.
    """
    value = _get_setting(REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in _TRUTHY


def _parse_versioned_keys(key_str):
    """Parse a ``version:key[,version:key...]`` string.

    Returns ``{version_int: key_bytes}``, or ``None`` when *key_str* is not
    in the versioned format. A bare base64 Fernet key never contains a
    colon, so the presence of ``:`` is an unambiguous marker.
    """
    if ':' not in key_str:
        return None
    keys = {}
    for part in key_str.split(','):
        part = part.strip()
        if not part:
            continue
        ver_str, sep, raw_key = part.partition(':')
        if not sep:
            raise ValidationError(
                "Keyring entry '%s' is missing its 'version:key' prefix." % part
            )
        ver_str = ver_str.strip()
        try:
            ver = int(ver_str)
        except ValueError:
            raise ValidationError(
                "Invalid key version '%s' in keyring configuration." % ver_str
            )
        keys[ver] = raw_key.strip().encode()
    return keys or None


def _keyring_from_string(key_str):
    """Build a keyring from ``version:key[,version:key...]`` or a bare key."""
    versioned = _parse_versioned_keys(key_str)
    if versioned is None:
        return EncryptionKeyring({0: Fernet(key_str.encode())})
    return EncryptionKeyring(
        {ver: Fernet(raw_key) for ver, raw_key in versioned.items()}
    )


def _keyring_from_payload(payload):
    """Build a keyring from a file payload, or ``None`` when it is empty.

    Accepts a JSON object of ``{"version": "key"}``, or the same text form the
    config provider takes. In the text form entries may be separated by commas
    or newlines, and ``#`` comments and blank lines are ignored, so the file
    stays readable when a secret manager renders it.
    """
    payload = payload.strip()
    if not payload:
        return None

    if payload.startswith('{'):
        try:
            data = json.loads(payload)
        except ValueError as err:
            raise ValidationError("Keyring JSON is not valid: %s" % err)
        if not isinstance(data, dict) or not data:
            raise ValidationError(
                "Keyring JSON must be a non-empty object of version -> key."
            )
        keys = {}
        for ver, raw_key in data.items():
            try:
                version = int(ver)
            except (TypeError, ValueError):
                raise ValidationError(
                    "Invalid key version '%s' in keyring JSON." % ver
                )
            keys[version] = Fernet(str(raw_key).strip().encode())
        return EncryptionKeyring(keys)

    entries = [
        line.strip() for line in payload.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]
    if not entries:
        return None
    return _keyring_from_string(','.join(entries))


def _load_keyring_from_file():
    """Build a keyring from a file on disk.

    The path comes from ``rec_encryption_key_path`` /
    ``REC_ENCRYPTION_KEY_PATH``. This is the portable provider: anything that
    can put a file somewhere can supply the keys — a mounted Kubernetes
    secret, a CSI driver for AWS/Azure/GCP, a Vault Agent template, or a SOPS
    decryption step.

    The file is re-read like any other externally managed source, so replacing
    it in place rotates keys without editing configuration. Mount the
    directory rather than the file when using Kubernetes: a ``subPath`` mount
    is not refreshed when the secret changes.
    """
    path = _get_setting(REC_ENCRYPTION_KEY_PATH)
    if not path:
        raise ValidationError(
            "File key provider requires '%s' in the config file or the %s "
            "environment variable."
            % (REC_ENCRYPTION_KEY_PATH, REC_ENCRYPTION_KEY_PATH.upper())
        )

    try:
        with open(path, 'r') as key_file:
            payload = key_file.read()
    except OSError as err:
        raise ValidationError(
            "Could not read the encryption keyring at '%s': %s" % (path, err)
        )

    keyring = _keyring_from_payload(payload)
    if keyring is None:
        raise ValidationError(
            "The encryption keyring at '%s' is empty." % path
        )

    _logger.info(
        "Loaded encryption keyring from %s: %d key(s), current version %d.",
        path, len(keyring), keyring.current_version,
    )
    return keyring


def _load_keyring_from_config():
    """Build a keyring from the ``rec_encryption_key`` config/env value.

    Supports two shapes:

    **Single key** (backward compatible)::

        rec_encryption_key = <base64-fernet-key>

    Loaded as version ``0``, which is also the version assumed for
    headerless legacy blobs.

    **Multi-key keyring** (for rotation)::

        rec_encryption_key = 0:<key0>,1:<key1>,2:<key2>

    The highest version is the current encryption key. A single versioned
    entry (``2:<key2>``) is valid too.
    """
    key_str = _get_setting(REC_ENCRYPTION_KEY)
    if not key_str:
        # Plain (untranslated) string: this can be raised before any
        # registry/env is available, where _() cannot be used.
        raise ValidationError(
            "Encryption key is not configured. Set '%s' in the Odoo config "
            "file or the %s environment variable. Encrypted fields (e.g. "
            "OAuth client secrets and tokens) cannot be read without it."
            % (REC_ENCRYPTION_KEY, REC_ENCRYPTION_KEY.upper())
        )

    keyring = _keyring_from_string(key_str.strip())

    if len(keyring) > 1:
        _logger.info(
            "Loaded encryption keyring from config: %d key(s), current version %d.",
            len(keyring), keyring.current_version,
        )

    return keyring


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
            "The library 'google-cloud-secret-manager' is missing. "
            "Install it with: pip install google-cloud-secret-manager"
        )

    project = _get_setting(GCP_PROJECT)
    if not project:
        raise ValidationError(
            "GCP key provider requires '%s' in the config file or the %s "
            "environment variable." % (GCP_PROJECT, GCP_PROJECT.upper())
        )

    secret_id = _get_setting(GCP_SECRET_NAME)
    if not secret_id:
        raise ValidationError(
            "GCP key provider requires '%s' in the config file or the %s "
            "environment variable." % (GCP_SECRET_NAME, GCP_SECRET_NAME.upper())
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
            "No valid Fernet keys found in GCP secret '%s' (project '%s')."
            % (secret_id, project)
        )

    _logger.info(
        "Loaded encryption keyring from GCP Secret Manager: "
        "%d key(s), current version %d.",
        len(keys), max(keys),
    )
    return EncryptionKeyring(keys)


_KEY_PROVIDERS = {
    "config": _load_keyring_from_config,
    "file": _load_keyring_from_file,
    "gcp_secret_manager": _load_keyring_from_gcp,
}


def _load_keyring():
    if Fernet is None:
        raise UserError(
            "The library 'cryptography' is missing, Fernet import cannot proceed."
        )

    provider_name = _get_setting(REC_ENCRYPTION_KEY_PROVIDER, "config")
    provider_fn = _KEY_PROVIDERS.get(provider_name)
    if provider_fn is None:
        raise ValidationError(
            "Unknown encryption key provider '%s'. Available: %s"
            % (provider_name, ", ".join(sorted(_KEY_PROVIDERS)))
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


def reload_keyring():
    """Re-read the key source and return the new keyring.

    The cache is replaced only on success, so a key source that is temporarily
    unreachable leaves the process running on the keyring it already had
    instead of dropping it.
    """
    global _keyring_instance
    keyring = _load_keyring()
    _keyring_instance = keyring
    return keyring


def set_keyring(keyring):
    """Install *keyring* as the cached one, used to undo a reload."""
    global _keyring_instance
    _keyring_instance = keyring


def current_key_provider():
    return _get_setting(REC_ENCRYPTION_KEY_PROVIDER, "config")


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
        if isinstance(values, UndecryptableData):
            # Saving would write back a dict containing only this field,
            # re-encrypted with the current key, silently discarding every other
            # encrypted field sharing the blob -- and unlike the read failure,
            # that cannot be undone by recovering the key.
            raise UserError(
                "Cannot save '%s': the encrypted data on this record could not "
                "be decrypted, and saving would permanently discard the other "
                "encrypted fields stored alongside it. Restore the key version "
                "this record was encrypted with, then try again."
                % (self.string or self.name)
            )
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
        # migrate_fields_to_encryption() builds a bare Encryption() that never
        # goes through field setup, so it has no name to report.
        field_name = getattr(self, 'name', None) or 'encrypted data'
        try:
            fernet = keyring.fernet_for_version(version)
        except ValidationError:
            raise DecryptFailed(
                "%s was encrypted with key version %s, which is not in the "
                "keyring. The data cannot be read." % (field_name, version),
                key_version=version,
            )
        try:
            return fernet.decrypt(ciphertext).decode()
        except InvalidToken:
            raise DecryptFailed(
                "%s was encrypted with a different key than the one held for "
                "version %s. Unless the previous key can be recovered, this "
                "data is unreadable." % (field_name, version),
                key_version=version,
            )

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
        if not value:
            return {}
        try:
            return json.loads(self._decrypt_data(value))
        except DecryptFailed as err:
            # Reading stays tolerant: the record is still usable and the rest of
            # the system keeps working. Writing is what has to be blocked, and
            # the marker type is how _inverse_encrypt knows to.
            _logger.error("%s.%s: %s", self.model_name, self.name, err)
            return UndecryptableData()

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
    # Also set it on the registry class. Models that inherit this one pick the
    # storage field up from the class, so without this an inherited encrypt
    # field has nowhere to store its value and the reflected ir.model.fields
    # row for the child is orphaned. It does leak the attribute into related
    # model classes, which Registry.reset_changes() does not undo; the test
    # suite sweeps that up rather than the other way round.
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


def _find_encryption_columns_sql(cr):
    """Candidate encryption columns taken from the database alone.

    Used when no registry is available (migration scripts, ``odoo shell``
    against a half-loaded database), and as a supplement otherwise. Covers
    both conventionally named columns and custom names declared in
    ``ir.model.fields``. Candidates are not guaranteed to exist; callers
    filter them through :func:`_filter_existing_columns`.
    """
    columns = set()
    cr.execute(
        """
        SELECT c.table_name, c.column_name
          FROM information_schema.columns c
          JOIN information_schema.tables t
            ON t.table_schema = c.table_schema
           AND t.table_name = c.table_name
         WHERE c.table_schema = current_schema()
           AND t.table_type = 'BASE TABLE'
           AND c.udt_name = 'bytea'
           AND c.column_name = %s
        """,
        (DEFAULT_ENCRYPTION_FIELD,),
    )
    columns.update((row[0], row[1]) for row in cr.fetchall())

    cr.execute(
        "SELECT to_regclass('ir_model_fields') IS NOT NULL "
        "AND to_regclass('ir_model') IS NOT NULL"
    )
    if not cr.fetchone()[0]:
        return columns

    cr.execute(
        """
        SELECT m.model, f.name
          FROM ir_model_fields f
          JOIN ir_model m ON m.id = f.model_id
         WHERE f.ttype = 'encryption'
        """
    )
    for model_name, field_name in cr.fetchall():
        # Best-effort table name; models with a custom _table are picked up
        # from the registry instead, and wrong guesses are filtered out.
        table = (model_name or '').replace('.', '_')
        if table and field_name:
            columns.add((table, field_name))
    return columns


def _filter_existing_columns(cr, pairs):
    """Keep only the ``(table, column)`` pairs that really exist as ``bytea``.

    Discovery can legitimately propose columns that are not in the database:
    a model whose table has not been created yet during an install, a field
    added by a module whose update has not run, or a guessed table name.
    Handing those to ``re_encrypt_table()`` would raise on a missing relation
    and abort the whole rotation, so they are dropped here instead.
    """
    if not pairs:
        return set()
    cr.execute(
        """
        SELECT c.table_name, c.column_name
          FROM information_schema.columns c
          JOIN information_schema.tables t
            ON t.table_schema = c.table_schema
           AND t.table_name = c.table_name
         WHERE c.table_schema = current_schema()
           AND t.table_type = 'BASE TABLE'
           AND c.udt_name = 'bytea'
           AND (c.table_name, c.column_name) IN %s
        """,
        (tuple(sorted(pairs)),),
    )
    return {(row[0], row[1]) for row in cr.fetchall()}


def find_encryption_columns(cr, registry=None):
    """Return a sorted list of ``(table, column)`` pairs holding encrypted data.

    Discovery is by *field type* (``encryption``), so no table list has to be
    maintained by hand. The live registry is authoritative; the database
    catalog is used as a supplement so that tables belonging to uninstalled
    or not-yet-loaded modules are still rotated. Everything is then verified
    against the catalog, so every returned pair is safe to query.

    Pass *registry* (e.g. ``env.registry``) whenever you have one, to avoid
    triggering a registry load from a bare cursor.
    """
    candidates = set()

    if registry is None:
        try:
            from odoo.modules.registry import Registry
            registry = Registry(cr.dbname)
        except Exception as err:  # pragma: no cover
            _logger.debug("No registry available for encryption discovery: %s", err)
            registry = None

    if registry is not None:
        for model in registry.models.values():
            if getattr(model, '_abstract', False):
                continue
            table = getattr(model, '_table', None)
            if not table:
                continue
            for fname, field in model._fields.items():
                if field.type == 'encryption':
                    candidates.add((table, fname))

    try:
        candidates |= _find_encryption_columns_sql(cr)
    except Exception as err:  # pragma: no cover
        _logger.debug("Catalog scan for encryption columns failed: %s", err)

    return sorted(_filter_existing_columns(cr, candidates))


def _pending_where(column):
    """SQL predicate matching rows that are *not* on the current key version.

    The version lives in the first three bytes, so this filters without
    decrypting anything. ``CASE`` is used rather than a chain of ``OR``s
    because PostgreSQL may evaluate ``OR`` arms in any order, and
    ``get_byte()`` raises on a blob shorter than the header.
    """
    return (
        '"{col}" IS NOT NULL AND CASE'
        ' WHEN octet_length("{col}") < {size} THEN TRUE'
        ' WHEN get_byte("{col}", 0) <> {fmt} THEN TRUE'
        ' ELSE (get_byte("{col}", 1) * 256 + get_byte("{col}", 2)) < %s'
        ' END'
    ).format(col=column, size=_HEADER_STRUCT.size, fmt=_HEADER_FORMAT)


def pending_re_encrypt_count(cr, table, encryption_field=None):
    """Number of rows in *table* still encrypted with an older key version."""
    encryption_field = encryption_field or DEFAULT_ENCRYPTION_FIELD
    current = get_keyring().current_version
    cr.execute(
        'SELECT count(*) FROM "{table}" WHERE {where}'.format(
            table=table, where=_pending_where(encryption_field),
        ),
        (current,),
    )
    return cr.fetchone()[0]


def encryption_version_histogram(cr, registry=None, columns=None):
    """Count stored blobs per key version, per column.

    Returns ``{(table, column): {version: count}}``, omitting empty columns.

    The version is read from the header in SQL, so nothing is decrypted and no
    keyring is required. That matters when planning a provider migration: the
    versions listed here are exactly the ones the new provider has to supply,
    and this still works when the current configuration cannot load a key.
    """
    if columns is None:
        columns = find_encryption_columns(cr, registry=registry)
    result = {}
    for table, column in columns:
        cr.execute(
            'SELECT CASE'
            ' WHEN octet_length("{col}") < {size} THEN 0'
            ' WHEN get_byte("{col}", 0) <> {fmt} THEN 0'
            ' ELSE get_byte("{col}", 1) * 256 + get_byte("{col}", 2)'
            ' END AS version, count(*) FROM "{table}"'
            ' WHERE "{col}" IS NOT NULL GROUP BY 1 ORDER BY 1'.format(
                col=column, table=table,
                size=_HEADER_STRUCT.size, fmt=_HEADER_FORMAT,
            )
        )
        counts = {row[0]: row[1] for row in cr.fetchall()}
        if counts:
            result[(table, column)] = counts
    return result


def re_encrypt_table(cr, table, encryption_field=None,
                     batch_size=DEFAULT_REENCRYPT_BATCH_SIZE,
                     skip_locked=False, commit=False, deadline=None,
                     lock_check=None):
    """Re-encrypt rows in *table* that are behind the current key version.

    Rows are selected in batches of *batch_size* using keyset pagination, and
    each batch is written with a single ``UPDATE``. Rows already on the current
    version are excluded in SQL, so repeated passes are cheap and no ciphertext
    is fetched needlessly.

    The defaults do the whole table in the caller's transaction, which is what
    you want at startup or in a maintenance window. The remaining arguments
    make the pass co-operative enough to run against a live system:

    :param skip_locked: add ``FOR UPDATE SKIP LOCKED`` so rows currently being
        written by someone else are left for a later run instead of blocking.
    :param commit: commit after every batch, so row locks are released
        promptly and completed work survives an interruption.
    :param deadline: ``time.monotonic()`` value at which to stop and return,
        leaving the rest for a later run.
    :param lock_check: callable invoked before each batch; when it returns a
        false value the pass stops. Used to re-take a transaction-scoped
        advisory lock after each commit.

    Returns the number of rows that were actually updated.
    """
    encryption_field = encryption_field or DEFAULT_ENCRYPTION_FIELD
    current = get_keyring().current_version
    select = (
        'SELECT id, "{col}" FROM "{table}" WHERE {where} AND id > %s '
        'ORDER BY id LIMIT %s'
    ).format(
        col=encryption_field, table=table,
        where=_pending_where(encryption_field),
    )
    if skip_locked:
        select += ' FOR UPDATE SKIP LOCKED'

    updated = 0
    failed = 0
    last_id = 0
    while True:
        if deadline is not None and time.monotonic() >= deadline:
            _logger.info(
                "Re-encryption of %s.%s reached its time budget after %d row(s); "
                "the rest will be done on the next run.",
                table, encryption_field, updated,
            )
            break
        if lock_check is not None and not lock_check():
            _logger.info(
                "Re-encryption of %s.%s stopped after %d row(s): the lock is "
                "held elsewhere.",
                table, encryption_field, updated,
            )
            break

        cr.execute(select, (current, last_id, batch_size))
        rows = cr.fetchall()
        if not rows:
            break
        last_id = rows[-1][0]

        ids, blobs = [], []
        for rec_id, raw in rows:
            raw = bytes(raw) if isinstance(raw, memoryview) else raw
            try:
                changed, new_blob = re_encrypt_blob(raw)
            except (ValidationError, InvalidToken, DecryptFailed) as err:
                # One unreadable row must not abort the table. Aborting leaves
                # the rotation permanently stuck with nothing to say about which
                # row is at fault; skipping means the pass completes and the
                # version histogram names the damage precisely. The row keeps
                # its old key version, so the rotation is still reported as
                # incomplete and no key can be retired on its account.
                failed += 1
                _logger.error(
                    "Could not re-encrypt %s.%s row %s: %s",
                    table, encryption_field, rec_id, err,
                )
                continue
            if changed:
                ids.append(rec_id)
                blobs.append(new_blob)

        if ids:
            cr.execute(
                'UPDATE "{table}" AS t SET "{col}" = d.blob '
                'FROM unnest(%s::bigint[], %s::bytea[]) AS d(id, blob) '
                'WHERE t.id = d.id'.format(table=table, col=encryption_field),
                (ids, blobs),
            )
            updated += len(ids)

        if commit:
            cr.commit()

    if failed:
        _logger.error(
            "Re-encryption of %s.%s left %d row(s) unreadable; they keep their "
            "current key version and the rotation cannot be considered complete.",
            table, encryption_field, failed,
        )
    return updated


def re_encrypt_all(cr, registry=None, batch_size=DEFAULT_REENCRYPT_BATCH_SIZE,
                   columns=None, skip_locked=False, commit=False,
                   deadline=None, lock_check=None):
    """Discover every encryption column and re-encrypt it to the current key.

    Extra arguments are passed to :func:`re_encrypt_table`.

    Returns ``{(table, column): rows_updated}``.
    """
    if columns is None:
        columns = find_encryption_columns(cr, registry=registry)
    results = {}
    started = time.time()
    for table, column in columns:
        updated = re_encrypt_table(
            cr, table, encryption_field=column, batch_size=batch_size,
            skip_locked=skip_locked, commit=commit, deadline=deadline,
            lock_check=lock_check,
        )
        results[(table, column)] = updated
        if updated:
            _logger.info("Re-encrypted %d row(s) in %s.%s.", updated, table, column)
    _logger.info(
        "Re-encryption pass over %d column(s) finished in %.1fs, %d row(s) rewritten.",
        len(results), time.time() - started, sum(results.values()),
    )
    return results


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
            try:
                data = json.loads(enc._decrypt_data(existing_blob))
            except DecryptFailed as err:
                # Continuing would merge the plaintext columns into an empty
                # dict and re-encrypt that over the existing blob -- and with
                # drop_columns the source data goes too. Fail the migration.
                raise UserError(
                    "Cannot migrate %s row %s into '%s': %s Migrating would "
                    "discard the encrypted data already stored there."
                    % (table, rec_id, encryption_field, err)
                )
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
