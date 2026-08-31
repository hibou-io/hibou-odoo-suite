import json
import os

from cryptography.fernet import Fernet

from odoo.tests import TransactionCase, tagged

from odoo.addons.hibou_field_encryption.models.fields import (
    DEFAULT_ENCRYPTION_FIELD,
    Encryption,
    REC_ENCRYPTION_KEY,
    _unpack_header,
    find_encryption_columns,
    get_keyring,
    reset_keyring,
)

from odoo.addons.hibou_field_encryption.tests.test_base_encryption import (
    ALL_CONFIG_KEYS,
    TEST_KEY,
    _restore,
    _save_and_clear,
)


class EncryptFieldsCase(TransactionCase):

    def setUp(self):
        super().setUp()
        self._saved = _save_and_clear(*ALL_CONFIG_KEYS)
        os.environ[REC_ENCRYPTION_KEY.upper()] = TEST_KEY
        reset_keyring()

    def tearDown(self):
        _restore(self._saved)
        reset_keyring()
        super().tearDown()


@tagged("post_install", "-at_install")
class TestEncryptFieldsExplicit(EncryptFieldsCase):

    def test_write_and_read_single_field(self):
        partner = self.env["res.partner"].create(
            {"name": "Test", "secret_note": "hello"}
        )
        self.assertEqual(partner.secret_note, "hello")

    def test_write_and_read_multiple_fields(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "note1",
            "secret_code": "code1",
        })
        self.assertEqual(partner.secret_note, "note1")
        self.assertEqual(partner.secret_code, "code1")

    def test_shared_blob(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "note1",
            "secret_code": "code1",
        })
        blob = partner.my_blob
        self.assertEqual(blob["secret_note"], "note1")
        self.assertEqual(blob["secret_code"], "code1")

    def test_update_field(self):
        partner = self.env["res.partner"].create(
            {"name": "Test", "secret_note": "v1"}
        )
        partner.secret_note = "v2"
        self.assertEqual(partner.secret_note, "v2")

    def test_clear_field(self):
        partner = self.env["res.partner"].create({
            "name": "Test",
            "secret_note": "value",
            "secret_code": "keep",
        })
        partner.secret_note = False
        self.assertFalse(partner.secret_note)
        self.assertEqual(partner.secret_code, "keep")

    def test_stored_blob_is_encrypted(self):
        """The column must not hold anything resembling the plaintext."""
        partner = self.env["res.partner"].create(
            {"name": "Test", "secret_note": "plaintext_marker"}
        )
        # create() sets the blob in the ORM cache; it only reaches Postgres
        # on flush, and this reads the column directly.
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT my_blob FROM res_partner WHERE id = %s", (partner.id,)
        )
        raw = bytes(self.env.cr.fetchone()[0])
        self.assertNotIn(b"plaintext_marker", raw)
        ver, _ = _unpack_header(raw)
        self.assertEqual(ver, 0)


@tagged("post_install", "-at_install")
class TestEncryptTrueSugar(EncryptFieldsCase):

    def test_auto_encryption_field_created(self):
        model = self.env["enc.test.sugar"]
        self.assertIn(DEFAULT_ENCRYPTION_FIELD, model._fields)
        self.assertIsInstance(
            model._fields[DEFAULT_ENCRYPTION_FIELD], Encryption,
        )

    def test_encrypt_true_read_write(self):
        rec = self.env["enc.test.sugar"].create({
            "name": "Test",
            "secret_one": "alpha",
            "secret_two": "beta",
        })
        self.assertEqual(rec.secret_one, "alpha")
        self.assertEqual(rec.secret_two, "beta")

    def test_encrypt_true_shared_blob(self):
        rec = self.env["enc.test.sugar"].create({
            "name": "Test",
            "secret_one": "alpha",
            "secret_two": "beta",
        })
        blob = rec[DEFAULT_ENCRYPTION_FIELD]
        self.assertEqual(blob.get("secret_one"), "alpha")
        self.assertEqual(blob.get("secret_two"), "beta")

    def test_encrypt_true_update(self):
        rec = self.env["enc.test.sugar"].create(
            {"name": "Test", "secret_one": "v1"}
        )
        rec.secret_one = "v2"
        self.assertEqual(rec.secret_one, "v2")


@tagged("post_install", "-at_install")
class TestInheritedEncryptFields(EncryptFieldsCase):
    """An _inherits pair with a custom named blob.

    This is the shape that broke in production when the storage field stopped
    being set on the registry class: Odoo's _add_field() raises for an
    inherited field that is not an attribute of the child's Python class.
    """

    def test_parent_has_the_named_blob(self):
        model = self.env["enc.test.group"]
        self.assertIn("group_blob", model._fields)
        self.assertIsInstance(model._fields["group_blob"], Encryption)

    def test_child_inherits_the_encrypt_fields(self):
        model = self.env["enc.test.member"]
        self.assertIn("group_secret", model._fields)
        self.assertIn("group_blob", model._fields)

    def test_child_reads_and_writes_through_the_parent(self):
        member = self.env["enc.test.member"].create({
            "label": "m1",
            "name": "g1",
            "group_secret": "through_child",
        })
        self.assertEqual(member.group_secret, "through_child")
        self.assertEqual(member.group_id.group_secret, "through_child")

        member.group_secret = "updated"
        self.assertEqual(member.group_id.group_secret, "updated")

    def test_parent_write_is_visible_from_the_child(self):
        group = self.env["enc.test.group"].create(
            {"name": "g2", "group_secret": "set_on_parent"}
        )
        member = self.env["enc.test.member"].create(
            {"label": "m2", "group_id": group.id}
        )
        self.assertEqual(member.group_secret, "set_on_parent")

    def test_both_fields_share_one_blob(self):
        group = self.env["enc.test.group"].create({
            "name": "g3",
            "group_secret": "one",
            "group_token": "two",
        })
        self.assertEqual(group.group_blob["group_secret"], "one")
        self.assertEqual(group.group_blob["group_token"], "two")

    def test_blob_is_stored_on_the_parent_table(self):
        group = self.env["enc.test.group"].create(
            {"name": "g4", "group_secret": "stored_here"}
        )
        self.env.flush_all()
        self.env.cr.execute(
            'SELECT group_blob FROM enc_test_group WHERE id = %s', (group.id,)
        )
        raw = bytes(self.env.cr.fetchone()[0])
        self.assertNotIn(b"stored_here", raw)
        enc = Encryption()
        self.assertEqual(
            json.loads(enc._decrypt_data(raw))["group_secret"], "stored_here",
        )

    def test_discovery_finds_the_custom_named_column(self):
        columns = find_encryption_columns(
            self.env.cr, registry=self.env.registry,
        )
        self.assertIn(("enc_test_group", "group_blob"), columns)


@tagged("post_install", "-at_install")
class TestBlobInspector(EncryptFieldsCase):
    """The inspector has to report the blob that is really on the row.

    The form view is the only place a rotation can be watched by hand, so an
    inspector that reports "no stored blob" for a populated row is worse than
    having none at all.
    """

    def test_reports_the_stored_blob(self):
        rec = self.env["enc.test.sugar"].create(
            {"name": "g", "secret_one": "alpha"}
        )
        self.assertFalse(rec.blob_is_empty)
        self.assertEqual(rec.blob_key_version, 0)
        self.assertTrue(rec.blob_bytes)

    def test_reports_an_empty_row_as_empty(self):
        rec = self.env["enc.test.sugar"].create({"name": "no secrets"})
        self.assertTrue(rec.blob_is_empty)
        self.assertEqual(rec.blob_bytes, 0)

    def test_reports_the_stored_blob_for_a_new_id_record(self):
        """Onchange computes against a NewId whose id is not the row id.

        This is what the form view does on every edit, and reading it through
        record.id rather than its origin made every populated row report
        itself as empty.
        """
        rec = self.env["enc.test.sugar"].create(
            {"name": "g", "secret_one": "alpha"}
        )
        pseudo = self.env["enc.test.sugar"].new(
            {"name": "edited"}, origin=rec,
        )
        self.assertFalse(pseudo.blob_is_empty)
        self.assertEqual(pseudo.blob_key_version, rec.blob_key_version)
        self.assertEqual(pseudo.blob_bytes, rec.blob_bytes)

    def test_custom_named_blob_is_inspected(self):
        group = self.env["enc.test.group"].create(
            {"name": "g", "group_secret": "one"}
        )
        self.assertFalse(group.blob_is_empty)
        self.assertTrue(group.blob_bytes)

    def test_pure_new_record_has_no_stored_blob(self):
        pseudo = self.env["enc.test.sugar"].new({"secret_one": "alpha"})
        self.assertTrue(pseudo.blob_is_empty)
        self.assertEqual(pseudo.blob_bytes, 0)
