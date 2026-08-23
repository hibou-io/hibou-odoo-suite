import json
import os
import tempfile
import time
from unittest.mock import patch

from cryptography.fernet import Fernet

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools.config import config

from odoo.addons.hibou_field_encryption.models.fields import (
    DEFAULT_ENCRYPTION_FIELD,
    REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT,
    REC_ENCRYPTION_KEY,
    REC_ENCRYPTION_KEY_PATH,
    REC_ENCRYPTION_KEY_PROVIDER,
    _pack_header,
    _parse_versioned_keys,
    _unpack_header,
    auto_reencrypt_disabled,
    current_key_provider,
    encryption_version_histogram,
    find_encryption_columns,
    get_keyring,
    pending_re_encrypt_count,
    re_encrypt_all,
    re_encrypt_table,
    reset_keyring,
)
from odoo.addons.hibou_field_encryption.models import models as enc_models
from odoo.addons.hibou_field_encryption.models.models import ICP_ENCRYPTION_KEY_VERSION

from .test_base_encryption import (
    ALL_CONFIG_KEYS,
    TEST_KEY,
    _restore,
    _save_and_clear,
)


# --------------------------------------------------------------------------
# Keyring config string parsing
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestKeyringParsing(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def test_bare_key_is_not_versioned(self):
        self.assertIsNone(_parse_versioned_keys(TEST_KEY))

    def test_single_versioned_key_is_parsed(self):
        """Regression: a keyring with one versioned entry and no comma used to
        fall through to Fernet('1:<key>') and crash at startup, which broke the
        documented final step of a rotation (dropping the retired key).
        """
        parsed = _parse_versioned_keys(f"1:{TEST_KEY}")
        self.assertEqual(parsed, {1: TEST_KEY.encode()})

    def test_single_versioned_key_loads(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"7:{TEST_KEY}"
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(len(kr), 1)
        self.assertEqual(kr.current_version, 7)
        ct = kr.current_fernet.encrypt(b"x")
        self.assertEqual(Fernet(TEST_KEY.encode()).decrypt(ct), b"x")

    def test_retired_key_removal_after_rotation(self):
        """The full rotation lifecycle: bare key -> two versions -> new key only."""
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()

        os.environ[REC_ENCRYPTION_KEY.upper()] = k0
        reset_keyring()
        self.assertEqual(get_keyring().current_version, 0)

        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{k0},1:{k1}"
        reset_keyring()
        self.assertEqual(get_keyring().current_version, 1)

        os.environ[REC_ENCRYPTION_KEY.upper()] = f"1:{k1}"
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 1)
        self.assertNotIn(0, kr)

    def test_whitespace_is_ignored(self):
        k0 = Fernet.generate_key().decode()
        k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"  0 : {k0} , 1 : {k1}  "
        reset_keyring()
        kr = get_keyring()
        self.assertEqual(kr.current_version, 1)
        self.assertIn(0, kr)

    def test_trailing_comma_is_ignored(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"3:{TEST_KEY},"
        reset_keyring()
        self.assertEqual(get_keyring().current_version, 3)

    def test_invalid_version_raises(self):
        with self.assertRaises(ValidationError):
            _parse_versioned_keys(f"one:{TEST_KEY}")

    def test_entry_without_version_prefix_raises(self):
        with self.assertRaises(ValidationError):
            _parse_versioned_keys(f"0:{TEST_KEY},{TEST_KEY}")

    def test_config_file_takes_precedence_over_env(self):
        env_key = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = env_key
        config[REC_ENCRYPTION_KEY] = TEST_KEY
        reset_keyring()
        ct = get_keyring().current_fernet.encrypt(b"y")
        self.assertEqual(Fernet(TEST_KEY.encode()).decrypt(ct), b"y")


# --------------------------------------------------------------------------
# Auto re-encryption opt-out flag
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestAutoReEncryptFlag(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)

    def tearDown(self):
        _restore(self._saved)
        super().tearDown()

    def test_enabled_by_default(self):
        self.assertFalse(auto_reencrypt_disabled())

    def test_truthy_values_disable(self):
        for value in ('1', 'true', 'True', 'TRUE', 'yes', 'on', 'enabled'):
            os.environ[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT.upper()] = value
            self.assertTrue(auto_reencrypt_disabled(), value)

    def test_falsy_values_do_not_disable(self):
        for value in ('0', 'false', 'no', 'off', ''):
            os.environ[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT.upper()] = value
            self.assertFalse(auto_reencrypt_disabled(), value)

    def test_config_file_bool_disables(self):
        config[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT] = True
        self.assertTrue(auto_reencrypt_disabled())


# --------------------------------------------------------------------------
# Encryption column discovery
# --------------------------------------------------------------------------

class _FakeField:
    def __init__(self, ftype):
        self.type = ftype


class _FakeModel:
    _abstract = False

    def __init__(self, table, column):
        self._table = table
        self._fields = {
            'name': _FakeField('char'),
            column: _FakeField('encryption'),
        }


class _FakeRegistry:
    """Minimal stand-in for a registry, to feed discovery a column that is
    declared in Python but absent from the database.
    """

    def __init__(self, table, column=DEFAULT_ENCRYPTION_FIELD):
        self.models = {'fake.model': _FakeModel(table, column)}


@tagged("post_install", "-at_install")
class TestFindEncryptionColumns(TransactionCase):
    TABLE = "test_discovery_enc"
    OTHER_TABLE = "test_discovery_other"

    def setUp(self):
        super().setUp()
        cr = self.env.cr
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            '"{}" bytea'
            ")".format(self.TABLE, DEFAULT_ENCRYPTION_FIELD)
        )
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            "some_blob bytea, "
            '"{}" varchar'
            ")".format(self.OTHER_TABLE, DEFAULT_ENCRYPTION_FIELD)
        )

    def tearDown(self):
        cr = self.env.cr
        cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.OTHER_TABLE))
        super().tearDown()

    def test_returns_table_column_pairs(self):
        columns = find_encryption_columns(self.env.cr, registry=self.env.registry)
        self.assertIsInstance(columns, list)
        for entry in columns:
            self.assertEqual(len(entry), 2)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], str)

    def test_is_sorted_and_deduplicated(self):
        columns = find_encryption_columns(self.env.cr, registry=self.env.registry)
        self.assertEqual(columns, sorted(set(columns)))

    def test_finds_conventional_column_via_catalog(self):
        columns = find_encryption_columns(self.env.cr, registry=self.env.registry)
        self.assertIn((self.TABLE, DEFAULT_ENCRYPTION_FIELD), columns)

    def test_ignores_non_bytea_column_of_same_name(self):
        columns = find_encryption_columns(self.env.cr, registry=self.env.registry)
        self.assertNotIn((self.OTHER_TABLE, DEFAULT_ENCRYPTION_FIELD), columns)

    def test_ignores_unrelated_bytea_column(self):
        columns = find_encryption_columns(self.env.cr, registry=self.env.registry)
        self.assertNotIn((self.OTHER_TABLE, 'some_blob'), columns)

    def test_finds_registry_declared_fields(self):
        """Registry-declared encryption fields are returned, as long as the
        column really exists. Fields declared by a model whose table was never
        created (a test model from a rolled back transaction, or a module whose
        update has not run) are excluded by the catalog verification.
        """
        existing = set(
            find_encryption_columns(self.env.cr, registry=self.env.registry)
        )
        expected = set()
        for model in self.env.registry.models.values():
            if getattr(model, '_abstract', False) or not getattr(model, '_table', None):
                continue
            for fname, field in model._fields.items():
                if field.type == 'encryption':
                    expected.add((model._table, fname))

        self.env.cr.execute(
            """
            SELECT c.table_name, c.column_name
              FROM information_schema.columns c
             WHERE c.table_schema = current_schema()
               AND c.udt_name = 'bytea'
            """
        )
        real_columns = {(row[0], row[1]) for row in self.env.cr.fetchall()}
        self.assertTrue((expected & real_columns).issubset(existing))

    def test_registry_declared_column_is_returned_when_table_exists(self):
        columns = find_encryption_columns(
            self.env.cr, registry=_FakeRegistry(self.TABLE),
        )
        self.assertIn((self.TABLE, DEFAULT_ENCRYPTION_FIELD), columns)

    def test_registry_custom_table_name_is_used(self):
        """The registry path must use ``_table``, not the model name."""
        registry = _FakeRegistry(self.TABLE)
        columns = find_encryption_columns(self.env.cr, registry=registry)
        self.assertIn((self.TABLE, DEFAULT_ENCRYPTION_FIELD), columns)
        self.assertNotIn(('fake_model', DEFAULT_ENCRYPTION_FIELD), columns)

    def test_works_without_registry_argument(self):
        columns = find_encryption_columns(self.env.cr)
        self.assertIn((self.TABLE, DEFAULT_ENCRYPTION_FIELD), columns)

    def test_missing_table_is_filtered_out(self):
        """A field can be declared in the registry before its table exists
        (mid-install, or a rolled back test model). Handing that to
        re_encrypt_table() would abort the whole rotation on a missing
        relation, so discovery must drop it.
        """
        columns = find_encryption_columns(
            self.env.cr, registry=_FakeRegistry('no_such_table_zzz'),
        )
        self.assertNotIn(('no_such_table_zzz', DEFAULT_ENCRYPTION_FIELD), columns)

    def test_missing_column_on_existing_table_is_filtered_out(self):
        columns = find_encryption_columns(
            self.env.cr,
            registry=_FakeRegistry(self.TABLE, column='not_a_column'),
        )
        self.assertNotIn((self.TABLE, 'not_a_column'), columns)

    def test_every_returned_column_is_queryable(self):
        for table, column in find_encryption_columns(
            self.env.cr, registry=self.env.registry,
        ):
            self.env.cr.execute(
                'SELECT "{}" FROM "{}" LIMIT 0'.format(column, table)
            )

    def test_base_helper_matches_function(self):
        self.assertEqual(
            self.env['base']._find_encryption_tables(),
            find_encryption_columns(self.env.cr, registry=self.env.registry),
        )


# --------------------------------------------------------------------------
# Batching, pending-row accounting and the co-operative cron options
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestReEncryptBatching(TransactionCase):
    TABLE = "test_batch_reencrypt"
    TABLE_TWO = "test_batch_reencrypt_two"

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()
        cr = self.env.cr
        for table in (self.TABLE, self.TABLE_TWO):
            cr.execute(
                'CREATE TABLE IF NOT EXISTS "{}" ('
                "id SERIAL PRIMARY KEY, "
                '"{}" bytea'
                ")".format(table, DEFAULT_ENCRYPTION_FIELD)
            )

    def tearDown(self):
        cr = self.env.cr
        for table in (self.TABLE, self.TABLE_TWO):
            cr.execute('DROP TABLE IF EXISTS "{}"'.format(table))
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _insert(self, table, data_dict, key_version=0):
        fernet = get_keyring().fernet_for_version(key_version)
        ct = fernet.encrypt(json.dumps(data_dict).encode())
        blob = _pack_header(key_version) + ct
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                table, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def _versions(self, table):
        cr = self.env.cr
        cr.execute(
            'SELECT "{}" FROM "{}" ORDER BY id'.format(
                DEFAULT_ENCRYPTION_FIELD, table
            )
        )
        return [_unpack_header(bytes(row[0]))[0] for row in cr.fetchall()]

    def test_batch_smaller_than_row_count(self):
        for i in range(7):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        updated = re_encrypt_table(self.env.cr, self.TABLE, batch_size=2)
        self.assertEqual(updated, 7)
        self.assertEqual(self._versions(self.TABLE), [1] * 7)

    def test_batch_size_one(self):
        for i in range(3):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        updated = re_encrypt_table(self.env.cr, self.TABLE, batch_size=1)
        self.assertEqual(updated, 3)
        self.assertEqual(self._versions(self.TABLE), [1, 1, 1])

    def test_batch_preserves_payload_per_row(self):
        ids = [self._insert(self.TABLE, {"i": str(i)}, key_version=0) for i in range(5)]
        re_encrypt_table(self.env.cr, self.TABLE, batch_size=2)
        cr = self.env.cr
        for i, rid in enumerate(ids):
            cr.execute(
                'SELECT "{}" FROM "{}" WHERE id = %s'.format(
                    DEFAULT_ENCRYPTION_FIELD, self.TABLE
                ),
                (rid,),
            )
            ver, ct = _unpack_header(bytes(cr.fetchone()[0]))
            self.assertEqual(ver, 1)
            self.assertEqual(
                json.loads(Fernet(self.k1.encode()).decrypt(ct).decode()),
                {"i": str(i)},
            )

    def test_mixed_versions_in_one_batch(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        self._insert(self.TABLE, {"b": "2"}, key_version=1)
        self._insert(self.TABLE, {"c": "3"}, key_version=0)
        updated = re_encrypt_table(self.env.cr, self.TABLE, batch_size=10)
        self.assertEqual(updated, 2)
        self.assertEqual(self._versions(self.TABLE), [1, 1, 1])

    def test_null_blobs_are_skipped(self):
        cr = self.env.cr
        cr.execute('INSERT INTO "{}" ("{}") VALUES (NULL)'.format(
            self.TABLE, DEFAULT_ENCRYPTION_FIELD))
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        updated = re_encrypt_table(self.env.cr, self.TABLE, batch_size=2)
        self.assertEqual(updated, 1)

    def test_empty_table(self):
        self.assertEqual(re_encrypt_table(self.env.cr, self.TABLE), 0)

    def test_re_encrypt_all_covers_every_column(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        self._insert(self.TABLE_TWO, {"b": "2"}, key_version=0)
        results = re_encrypt_all(self.env.cr, registry=self.env.registry)
        self.assertEqual(results.get((self.TABLE, DEFAULT_ENCRYPTION_FIELD)), 1)
        self.assertEqual(results.get((self.TABLE_TWO, DEFAULT_ENCRYPTION_FIELD)), 1)
        self.assertEqual(self._versions(self.TABLE), [1])
        self.assertEqual(self._versions(self.TABLE_TWO), [1])

    def test_re_encrypt_all_honours_explicit_columns(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        self._insert(self.TABLE_TWO, {"b": "2"}, key_version=0)
        results = re_encrypt_all(
            self.env.cr,
            registry=self.env.registry,
            columns=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        )
        self.assertEqual(list(results), [(self.TABLE, DEFAULT_ENCRYPTION_FIELD)])
        self.assertEqual(self._versions(self.TABLE_TWO), [0])

    def test_re_encrypt_all_is_idempotent(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        re_encrypt_all(self.env.cr, registry=self.env.registry)
        results = re_encrypt_all(self.env.cr, registry=self.env.registry)
        self.assertEqual(results.get((self.TABLE, DEFAULT_ENCRYPTION_FIELD)), 0)

    # ----------------------------------------------------------------------
    # Pending-row accounting (SQL header filter, no decryption)
    # ----------------------------------------------------------------------

    def test_pending_count_includes_old_version(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        self.assertEqual(
            pending_re_encrypt_count(self.env.cr, self.TABLE), 1,
        )

    def test_pending_count_excludes_current_version(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=1)
        self.assertEqual(
            pending_re_encrypt_count(self.env.cr, self.TABLE), 0,
        )

    def test_pending_count_includes_legacy_headerless_blob(self):
        cr = self.env.cr
        legacy = Fernet(self.k0.encode()).encrypt(b'{"legacy": true}')
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s)'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (legacy,),
        )
        self.assertEqual(pending_re_encrypt_count(cr, self.TABLE), 1)

    def test_pending_count_tolerates_short_blob(self):
        """get_byte() raises past the end of a bytea, so the filter must not
        read the header of a blob shorter than three bytes.
        """
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s)'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (b'\x01',),
        )
        self.assertEqual(pending_re_encrypt_count(cr, self.TABLE), 1)

    def test_pending_count_ignores_nulls(self):
        cr = self.env.cr
        cr.execute('INSERT INTO "{}" ("{}") VALUES (NULL)'.format(
            self.TABLE, DEFAULT_ENCRYPTION_FIELD))
        self.assertEqual(pending_re_encrypt_count(cr, self.TABLE), 0)

    def test_version_histogram_counts_each_version(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        self._insert(self.TABLE, {"b": "2"}, key_version=0)
        self._insert(self.TABLE, {"c": "3"}, key_version=1)
        histogram = encryption_version_histogram(
            self.env.cr, columns=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        )
        self.assertEqual(
            histogram[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)], {0: 2, 1: 1},
        )

    def test_version_histogram_counts_legacy_and_short_blobs_as_zero(self):
        cr = self.env.cr
        legacy = Fernet(self.k0.encode()).encrypt(b'{"legacy": true}')
        for value in (legacy, b'\x01'):
            cr.execute(
                'INSERT INTO "{}" ("{}") VALUES (%s)'.format(
                    self.TABLE, DEFAULT_ENCRYPTION_FIELD
                ),
                (value,),
            )
        histogram = encryption_version_histogram(
            cr, columns=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        )
        self.assertEqual(
            histogram[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)], {0: 2},
        )

    def test_version_histogram_ignores_nulls_and_empty_columns(self):
        cr = self.env.cr
        cr.execute('INSERT INTO "{}" ("{}") VALUES (NULL)'.format(
            self.TABLE, DEFAULT_ENCRYPTION_FIELD))
        histogram = encryption_version_histogram(
            cr,
            columns=[
                (self.TABLE, DEFAULT_ENCRYPTION_FIELD),
                (self.TABLE_TWO, DEFAULT_ENCRYPTION_FIELD),
            ],
        )
        self.assertEqual(histogram, {})

    def test_version_histogram_after_pass_shows_one_version(self):
        """The check that says a provider migration is safe to make."""
        for i in range(3):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        re_encrypt_table(self.env.cr, self.TABLE)
        histogram = encryption_version_histogram(
            self.env.cr, columns=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        )
        self.assertEqual(
            histogram[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)], {1: 3},
        )

    def test_pending_count_drops_to_zero_after_pass(self):
        for i in range(4):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        re_encrypt_table(self.env.cr, self.TABLE, batch_size=2)
        self.assertEqual(
            pending_re_encrypt_count(self.env.cr, self.TABLE), 0,
        )

    # ----------------------------------------------------------------------
    # Co-operative options used by the cron
    # ----------------------------------------------------------------------

    def test_deadline_already_passed_does_nothing(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        updated = re_encrypt_table(
            self.env.cr, self.TABLE, deadline=time.monotonic() - 1,
        )
        self.assertEqual(updated, 0)
        self.assertEqual(self._versions(self.TABLE), [0])

    def test_deadline_in_future_completes(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        updated = re_encrypt_table(
            self.env.cr, self.TABLE, deadline=time.monotonic() + 300,
        )
        self.assertEqual(updated, 1)

    def test_deadline_stops_between_batches(self):
        for i in range(6):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        calls = []
        start = time.monotonic()

        def fake_monotonic():
            calls.append(1)
            # First check passes, every later check is past the deadline.
            return start if len(calls) <= 1 else start + 10

        with patch.object(time, 'monotonic', fake_monotonic):
            updated = re_encrypt_table(
                self.env.cr, self.TABLE, batch_size=2, deadline=start + 1,
            )
        self.assertEqual(updated, 2)
        self.assertEqual(pending_re_encrypt_count(self.env.cr, self.TABLE), 4)

    def test_lock_check_false_stops_immediately(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        updated = re_encrypt_table(
            self.env.cr, self.TABLE, lock_check=lambda: False,
        )
        self.assertEqual(updated, 0)
        self.assertEqual(self._versions(self.TABLE), [0])

    def test_lock_check_called_per_batch(self):
        for i in range(4):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        calls = []
        re_encrypt_table(
            self.env.cr, self.TABLE, batch_size=2,
            lock_check=lambda: calls.append(1) or True,
        )
        self.assertGreaterEqual(len(calls), 2)

    def test_skip_locked_still_updates_uncontended_rows(self):
        for i in range(3):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        updated = re_encrypt_table(
            self.env.cr, self.TABLE, skip_locked=True, batch_size=2,
        )
        self.assertEqual(updated, 3)
        self.assertEqual(self._versions(self.TABLE), [1, 1, 1])

    def test_skip_locked_skips_a_row_locked_by_another_session(self):
        """The claim the cron rests on: a row another transaction is writing is
        left for a later run instead of blocking the pass.

        Real contention needs a second connection, and rows written inside the
        test transaction are invisible to one, so this runs on its own table
        over independent connections and cleans up in finally blocks. The
        worker gets a statement timeout so a regression fails instead of
        hanging the suite.
        """
        from odoo.sql_db import db_connect

        table = "test_skip_locked_contention"
        dbname = self.env.cr.dbname
        fernet = get_keyring().fernet_for_version(0)
        blob = _pack_header(0) + fernet.encrypt(b'{"a": "1"}')

        setup_cr = db_connect(dbname).cursor()
        try:
            setup_cr.execute(
                'CREATE TABLE "{}" (id SERIAL PRIMARY KEY, "{}" bytea)'.format(
                    table, DEFAULT_ENCRYPTION_FIELD
                )
            )
            setup_cr.execute(
                'INSERT INTO "{}" ("{}") VALUES (%s), (%s)'.format(
                    table, DEFAULT_ENCRYPTION_FIELD
                ),
                (blob, blob),
            )
            setup_cr.commit()

            holder_cr = db_connect(dbname).cursor()
            worker_cr = db_connect(dbname).cursor()
            try:
                holder_cr.execute(
                    'SELECT id FROM "{}" ORDER BY id LIMIT 1 FOR UPDATE'.format(
                        table
                    )
                )
                locked_id = holder_cr.fetchone()[0]

                worker_cr.execute("SET statement_timeout = '5000'")
                updated = re_encrypt_table(
                    worker_cr, table, skip_locked=True, batch_size=10,
                )
                worker_cr.commit()
                self.assertEqual(updated, 1)
            finally:
                holder_cr.rollback()
                holder_cr.close()
                worker_cr.close()

            setup_cr.execute(
                'SELECT id, "{}" FROM "{}" ORDER BY id'.format(
                    DEFAULT_ENCRYPTION_FIELD, table
                )
            )
            versions = {
                row[0]: _unpack_header(bytes(row[1]))[0]
                for row in setup_cr.fetchall()
            }
            self.assertEqual(versions.pop(locked_id), 0)
            self.assertEqual(list(versions.values()), [1])
        finally:
            setup_cr.rollback()
            setup_cr.execute('DROP TABLE IF EXISTS "{}"'.format(table))
            setup_cr.commit()
            setup_cr.close()

    def test_commit_per_batch(self):
        for i in range(5):
            self._insert(self.TABLE, {"i": str(i)}, key_version=0)
        with patch.object(self.env.cr, 'commit') as mock_commit:
            updated = re_encrypt_table(
                self.env.cr, self.TABLE, batch_size=2, commit=True,
            )
        self.assertEqual(updated, 5)
        self.assertEqual(mock_commit.call_count, 3)

    def test_no_commit_by_default(self):
        self._insert(self.TABLE, {"a": "1"}, key_version=0)
        with patch.object(self.env.cr, 'commit') as mock_commit:
            re_encrypt_table(self.env.cr, self.TABLE)
        mock_commit.assert_not_called()


# --------------------------------------------------------------------------
# Automatic re-encryption at registry load
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestAutoReEncryptAtBoot(TransactionCase):
    TABLE = "test_boot_reencrypt"

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '0')
        cr = self.env.cr
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            '"{}" bytea'
            ")".format(self.TABLE, DEFAULT_ENCRYPTION_FIELD)
        )

    def tearDown(self):
        self.env.cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, False)
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _insert(self, data_dict, key_version=0):
        fernet = get_keyring().fernet_for_version(key_version)
        ct = fernet.encrypt(json.dumps(data_dict).encode())
        blob = _pack_header(key_version) + ct
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def _version_of(self, rec_id):
        cr = self.env.cr
        cr.execute(
            'SELECT "{}" FROM "{}" WHERE id = %s'.format(
                DEFAULT_ENCRYPTION_FIELD, self.TABLE
            ),
            (rec_id,),
        )
        return _unpack_header(bytes(cr.fetchone()[0]))[0]

    def _run_boot(self):
        """Run the startup pass without letting it commit the test transaction."""
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ), patch.object(self.env.cr, 'commit'):
            self.env['base']._auto_re_encrypt_fields()

    def test_runs_by_default(self):
        rid = self._insert({"secret": "rotate_me"}, key_version=0)
        self._run_boot()
        self.assertEqual(self._version_of(rid), 1)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1')

    def test_skipped_when_disabled(self):
        rid = self._insert({"secret": "leave_me"}, key_version=0)
        os.environ[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT.upper()] = '1'
        self._run_boot()
        self.assertEqual(self._version_of(rid), 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_skipped_for_single_key(self):
        os.environ[REC_ENCRYPTION_KEY.upper()] = self.k0
        reset_keyring()
        rid = self._insert({"secret": "single"}, key_version=0)
        self._run_boot()
        self.assertEqual(self._version_of(rid), 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_skipped_when_already_stamped(self):
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '1')
        rid = self._insert({"secret": "stamped"}, key_version=0)
        self._run_boot()
        self.assertEqual(self._version_of(rid), 0)

    def test_no_keyring_gracefully_skips(self):
        os.environ.pop(REC_ENCRYPTION_KEY.upper(), None)
        reset_keyring()
        self._run_boot()
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_does_not_stamp_on_failure(self):
        rid = self._insert({"secret": "boom"}, key_version=0)
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ), patch.object(self.env.cr, 'commit'), patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
            side_effect=Exception("db error"),
        ):
            self.env['base']._auto_re_encrypt_fields()
        self.assertEqual(self._version_of(rid), 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_second_run_is_a_noop(self):
        rid = self._insert({"secret": "once"}, key_version=0)
        self._run_boot()
        with patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
        ) as mock_re_encrypt:
            self._run_boot()
        mock_re_encrypt.assert_not_called()
        self.assertEqual(self._version_of(rid), 1)

    def test_manual_trigger_ignores_disable_flag(self):
        rid = self._insert({"secret": "manual"}, key_version=0)
        os.environ[REC_ENCRYPTION_DISABLE_AUTO_REENCRYPT.upper()] = '1'
        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ):
            self.assertTrue(self.env['base']._re_encrypt_now())
        self.assertEqual(self._version_of(rid), 1)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1')

    def test_manual_trigger_with_nothing_pending(self):
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '1')
        self.assertTrue(self.env['base']._re_encrypt_now())

    def test_does_not_stamp_when_a_straggler_appears_mid_pass(self):
        """A worker on an older cached keyring can write a stale row while the
        pass runs. Stamping then would declare the retired key safe to delete
        while that row still needs it.
        """
        self._insert({"secret": "first"}, key_version=0)

        def insert_straggler(*args, **kwargs):
            result = re_encrypt_table(*args, **kwargs)
            self._insert({"secret": "late"}, key_version=0)
            return result

        with patch.object(
            type(self.env['base']),
            '_find_encryption_tables',
            return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
        ), patch.object(self.env.cr, 'commit'), patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
            side_effect=insert_straggler,
        ):
            self.env['base']._auto_re_encrypt_fields()

        self.assertEqual(pending_re_encrypt_count(self.env.cr, self.TABLE), 1)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_rotation_pending_reports_current_version(self):
        self.assertEqual(self.env['base']._encryption_rotation_pending(), 1)
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '1')
        self.assertIsNone(self.env['base']._encryption_rotation_pending())

    def test_migrated_version_handles_garbage(self):
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, 'not-a-number')
        self.assertEqual(self.env['base']._encryption_migrated_version(), 0)

    def test_advisory_lock_prevents_concurrent_run(self):
        rid = self._insert({"secret": "locked"}, key_version=0)
        with patch.object(
            type(self.env['base']),
            '_try_re_encrypt_lock',
            return_value=False,
        ), patch.object(
            type(self.env['base']),
            '_re_encrypt_to_current_version',
        ) as mock_run:
            self.env['base']._auto_re_encrypt_fields()
        mock_run.assert_not_called()
        self.assertEqual(self._version_of(rid), 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_advisory_lock_is_granted_when_free(self):
        self.assertTrue(self.env['base']._try_re_encrypt_lock())

    def test_boot_reloads_the_keyring(self):
        """Registry load is where the key source is re-read, because it happens
        in every process.
        """
        with patch(
            'odoo.addons.hibou_field_encryption.models.models.reset_keyring',
        ) as mock_reset:
            self._run_boot()
        mock_reset.assert_called()

    def test_register_hook_triggers_auto_re_encrypt(self):
        with patch.object(
            type(self.env['base']),
            '_auto_re_encrypt_fields',
        ) as mock_auto:
            self.env['ir.model.fields']._register_hook()
        mock_auto.assert_called_once()

    def test_register_hook_swallows_errors(self):
        with patch.object(
            type(self.env['base']),
            '_auto_re_encrypt_fields',
            side_effect=Exception("boom"),
        ):
            self.env['ir.model.fields']._register_hook()


# --------------------------------------------------------------------------
# File key provider
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestFileKeyProvider(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "keyring")
        os.environ[REC_ENCRYPTION_KEY_PROVIDER.upper()] = "file"
        os.environ[REC_ENCRYPTION_KEY_PATH.upper()] = self.path

    def tearDown(self):
        for name in os.listdir(self.directory):
            os.unlink(os.path.join(self.directory, name))
        os.rmdir(self.directory)
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _write(self, payload):
        with open(self.path, "w") as key_file:
            key_file.write(payload)
        reset_keyring()

    def test_versioned_string(self):
        self._write(f"0:{self.k0},1:{self.k1}\n")
        kr = get_keyring()
        self.assertEqual(kr.versions, [0, 1])
        ct = kr.current_fernet.encrypt(b"x")
        self.assertEqual(Fernet(self.k1.encode()).decrypt(ct), b"x")

    def test_bare_key_is_version_zero(self):
        self._write(self.k0)
        self.assertEqual(get_keyring().versions, [0])

    def test_json_object(self):
        self._write(json.dumps({"0": self.k0, "1": self.k1}))
        self.assertEqual(get_keyring().versions, [0, 1])

    def test_newline_separated_entries(self):
        self._write(f"0:{self.k0}\n1:{self.k1}\n")
        self.assertEqual(get_keyring().versions, [0, 1])

    def test_comments_and_blank_lines_are_ignored(self):
        self._write(
            f"# retired\n0:{self.k0}\n\n# current\n1:{self.k1}\n"
        )
        self.assertEqual(get_keyring().versions, [0, 1])

    def test_missing_path_setting_raises(self):
        os.environ.pop(REC_ENCRYPTION_KEY_PATH.upper(), None)
        reset_keyring()
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_missing_file_raises(self):
        reset_keyring()
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_empty_file_raises(self):
        self._write("\n\n# only comments\n")
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_invalid_json_raises(self):
        self._write('{"0": ')
        with self.assertRaises(ValidationError):
            get_keyring()

    def test_rotating_by_replacing_the_file(self):
        """Hands-off rotation without a vendor: rewrite the file and the poll
        picks it up and tells the fleet, exactly as it does for GCP.
        """
        self._write(f"0:{self.k0},1:{self.k1}")
        self.assertEqual(get_keyring().versions, [0, 1])

        k2 = Fernet.generate_key().decode()
        with open(self.path, "w") as key_file:
            key_file.write(f"0:{self.k0},1:{self.k1},2:{k2}")

        with patch.object(
            type(self.env['base']), '_signal_registry_change',
            return_value=True,
        ) as mock_signal:
            self.assertTrue(self.env['base']._poll_key_source())
        mock_signal.assert_called_once()
        self.assertEqual(get_keyring().versions, [0, 1, 2])


# --------------------------------------------------------------------------
# Polling an externally managed key source
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestKeySourcePolling(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()
        # Load it now. The poll compares the reloaded key set against the one
        # this process already holds, so a keyring has to exist first;
        # otherwise get_keyring() lazily loads the *new* keys as the "before"
        # state and correctly reports that nothing changed.
        get_keyring()
        self.icp = self.env['ir.config_parameter'].sudo()
        # Already rotated, so these tests observe polling and nothing else.
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '1')

    def tearDown(self):
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, False)
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _pretend_gcp(self):
        return patch(
            'odoo.addons.hibou_field_encryption.models.models.current_key_provider',
            return_value='gcp_secret_manager',
        )

    def _add_third_version(self):
        k2 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = (
            f"0:{self.k0},1:{self.k1},2:{k2}"
        )

    def test_config_provider_is_not_polled(self):
        """A config value cannot change under a running process, so re-reading
        it would only risk getting ahead of the other workers.
        """
        self.assertEqual(current_key_provider(), 'config')
        with patch(
            'odoo.addons.hibou_field_encryption.models.models.reload_keyring',
        ) as mock_reload:
            self.assertFalse(self.env['base']._poll_key_source())
        mock_reload.assert_not_called()

    def test_no_signal_when_versions_are_unchanged(self):
        with self._pretend_gcp(), patch.object(
            type(self.env['base']), '_signal_registry_change',
        ) as mock_signal:
            self.assertFalse(self.env['base']._poll_key_source())
        mock_signal.assert_not_called()

    def test_new_version_signals_every_worker(self):
        self._add_third_version()
        with self._pretend_gcp(), patch.object(
            type(self.env['base']), '_signal_registry_change',
            return_value=True,
        ) as mock_signal:
            self.assertTrue(self.env['base']._poll_key_source())
        mock_signal.assert_called_once()
        self.assertEqual(get_keyring().versions, [0, 1, 2])

    def test_cron_defers_rotation_to_the_next_run(self):
        """The run that discovers a key version must not also rotate: the other
        workers have not reloaded yet.
        """
        self._add_third_version()
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '0')
        with self._pretend_gcp(), patch.object(
            type(self.env['base']), '_signal_registry_change',
            return_value=True,
        ), patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
        ) as mock_re_encrypt:
            self.env['base']._cron_re_encrypt_fields()
        mock_re_encrypt.assert_not_called()
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_unreachable_key_source_keeps_the_cached_keyring(self):
        with self._pretend_gcp(), patch(
            'odoo.addons.hibou_field_encryption.models.models.reload_keyring',
            side_effect=Exception("secret manager unreachable"),
        ):
            self.assertFalse(self.env['base']._poll_key_source())
        self.assertEqual(get_keyring().versions, [0, 1])

    def test_failed_signal_rolls_the_keyring_back(self):
        """Without a signal this process would be the only one on the new key."""
        self._add_third_version()
        with self._pretend_gcp(), patch.object(
            type(self.env['base']), '_signal_registry_change',
            return_value=False,
        ):
            self.assertFalse(self.env['base']._poll_key_source())
        self.assertEqual(get_keyring().versions, [0, 1])


# --------------------------------------------------------------------------
# Incremental cron pass
# --------------------------------------------------------------------------

@tagged("post_install", "-at_install")
class TestCronIncremental(TransactionCase):
    TABLE = "test_cron_incremental"

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        self.k0 = Fernet.generate_key().decode()
        self.k1 = Fernet.generate_key().decode()
        os.environ[REC_ENCRYPTION_KEY.upper()] = f"0:{self.k0},1:{self.k1}"
        reset_keyring()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, '0')
        cr = self.env.cr
        cr.execute(
            'CREATE TABLE IF NOT EXISTS "{}" ('
            "id SERIAL PRIMARY KEY, "
            '"{}" bytea'
            ")".format(self.TABLE, DEFAULT_ENCRYPTION_FIELD)
        )

    def tearDown(self):
        self.env.cr.execute('DROP TABLE IF EXISTS "{}"'.format(self.TABLE))
        self.icp.set_param(ICP_ENCRYPTION_KEY_VERSION, False)
        _restore(self._saved)
        reset_keyring()
        super().tearDown()

    def _insert(self, data_dict, key_version=0):
        fernet = get_keyring().fernet_for_version(key_version)
        ct = fernet.encrypt(json.dumps(data_dict).encode())
        blob = _pack_header(key_version) + ct
        cr = self.env.cr
        cr.execute(
            'INSERT INTO "{}" ("{}") VALUES (%s) RETURNING id'.format(
                self.TABLE, DEFAULT_ENCRYPTION_FIELD
            ),
            (blob,),
        )
        return cr.fetchone()[0]

    def _patches(self):
        return (
            patch.object(
                type(self.env['base']),
                '_find_encryption_tables',
                return_value=[(self.TABLE, DEFAULT_ENCRYPTION_FIELD)],
            ),
            # The cron commits each batch; Odoo forbids a real commit in a test.
            patch.object(self.env.cr, 'commit'),
        )

    def test_cron_does_not_reload_the_keyring(self):
        """The cron is a single process. If it re-read the key source it would
        rotate to a version the HTTP workers still know nothing about, and they
        would carry on writing with the old one.
        """
        self._insert({"secret": "inc"}, key_version=0)
        tables, commit = self._patches()
        with tables, commit, patch(
            'odoo.addons.hibou_field_encryption.models.models.reset_keyring',
        ) as mock_reset:
            self.env['base']._cron_re_encrypt_fields()
        mock_reset.assert_not_called()

    def test_cron_passes_cooperative_options(self):
        """The cron must not hold one long transaction against live traffic."""
        self._insert({"secret": "inc"}, key_version=0)
        tables, commit = self._patches()
        with tables, commit, patch(
            'odoo.addons.hibou_field_encryption.models.models.re_encrypt_table',
            return_value=0,
        ) as mock_re_encrypt:
            self.env['base']._cron_re_encrypt_fields()
        kwargs = mock_re_encrypt.call_args.kwargs
        self.assertTrue(kwargs['skip_locked'])
        self.assertTrue(kwargs['commit'])
        self.assertIsNotNone(kwargs['deadline'])
        self.assertIsNotNone(kwargs['lock_check'])

    def test_cron_does_not_stamp_while_rows_remain(self):
        """A budget-limited run must leave the rotation open, so the old key
        stays required until every row is converted.
        """
        self._insert({"secret": "slow"}, key_version=0)
        tables, commit = self._patches()
        with tables, commit, patch.object(
            enc_models, 'REENCRYPT_CRON_TIME_BUDGET', -1,
        ):
            self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(pending_re_encrypt_count(self.env.cr, self.TABLE), 1)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '0')

    def test_cron_resumes_after_partial_run(self):
        for i in range(4):
            self._insert({"i": str(i)}, key_version=0)

        tables, commit = self._patches()
        with tables, commit, patch.object(
            enc_models, 'REENCRYPT_CRON_TIME_BUDGET', -1,
        ):
            self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(pending_re_encrypt_count(self.env.cr, self.TABLE), 4)

        tables, commit = self._patches()
        with tables, commit:
            self.env['base']._cron_re_encrypt_fields()
        self.assertEqual(pending_re_encrypt_count(self.env.cr, self.TABLE), 0)
        self.assertEqual(self.icp.get_param(ICP_ENCRYPTION_KEY_VERSION), '1')
