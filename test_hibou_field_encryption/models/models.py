from odoo import api, fields, models

from odoo.addons.hibou_field_encryption.models.fields import (
    _unpack_header,
    get_keyring,
)


class EncryptionBlobInspector(models.AbstractModel):
    """Surfaces what is actually stored, so a rotation can be watched happening.

    The ORM only ever hands back the decrypted value, which looks identical
    before and after a rotation. These read the raw column instead: the key
    version in the blob header is the thing that actually changes, and it is
    what ``encryption_version_histogram()`` and the retire gate look at.

    Concrete models set ``_blob_field`` to the column holding their blob.
    """

    _name = "enc.test.blob.inspector"
    _description = "Encryption Blob Inspector"

    _blob_field = "rec_encrypted"

    blob_key_version = fields.Integer(
        string="Stored Key Version", compute="_compute_blob_info",
        help="Key version in the stored blob's header. This is what a rotation "
             "changes; the decrypted value looks the same either way.")
    blob_bytes = fields.Integer(
        string="Blob Size", compute="_compute_blob_info")
    blob_is_empty = fields.Boolean(
        string="No Stored Blob", compute="_compute_blob_info")
    keyring_versions = fields.Char(
        string="Keyring Versions", compute="_compute_keyring_info",
        help="Key versions this process currently holds. Cached per process, "
             "so it only changes at registry load.")
    keyring_current = fields.Integer(
        string="Current Key Version", compute="_compute_keyring_info",
        help="Version new writes are encrypted with. A row whose stored "
             "version is lower than this is still pending re-encryption.")
    blob_is_pending = fields.Boolean(
        string="Pending Re-encryption", compute="_compute_keyring_info")

    def _compute_blob_info(self):
        blob_field = self._blob_field
        # Onchange evaluates a form's computed fields against NewId records
        # originating from the saved row, so record.id is a NewId while the
        # blob is stored under the origin's integer id. self.ids already
        # resolves to origins, so the lookup has to as well; otherwise every
        # get() misses and a populated row reports itself as empty.
        origins = self._origin
        # the blob is a stored column, so pending writes have to reach the
        # database before the raw read below can see them
        origins.flush_recordset([blob_field])
        rows = {}
        if origins.ids:
            self.env.cr.execute(
                'SELECT id, "{}" FROM "{}" WHERE id IN %s'.format(
                    blob_field, self._table),
                (tuple(origins.ids),),
            )
            rows = dict(self.env.cr.fetchall())
        for record in self:
            raw = rows.get(record._origin.id)
            if isinstance(raw, memoryview):
                raw = bytes(raw)
            if not raw:
                record.blob_key_version = 0
                record.blob_bytes = 0
                record.blob_is_empty = True
                continue
            version, _ciphertext = _unpack_header(raw)
            record.blob_key_version = version
            record.blob_bytes = len(raw)
            record.blob_is_empty = False

    @api.depends("blob_key_version", "blob_is_empty")
    def _compute_keyring_info(self):
        try:
            keyring = get_keyring()
            versions = keyring.versions
            current = keyring.current_version
            label = ", ".join(str(v) for v in versions)
        except Exception as err:
            versions, current, label = [], 0, "unavailable: %s" % err
        for record in self:
            record.keyring_versions = label
            record.keyring_current = current
            record.blob_is_pending = bool(
                versions and not record.blob_is_empty
                and record.blob_key_version < current
            )

    def action_re_encrypt_now(self):
        """Rotate every encrypted column to the current key, right now.

        Ignores ``rec_encryption_disable_auto_reencrypt``, exactly as it does
        from a shell.
        """
        self.env["base"]._re_encrypt_now()
        return True

    def action_refresh(self):
        """Re-read the blobs, so the version column reflects a rotation."""
        self.invalidate_recordset()
        return True


class EncryptPartnerExplicit(models.Model):
    """An explicitly named blob on a model that other models _inherits.

    res.users delegates to res.partner, so this also covers the inherited
    case: Odoo copies these fields onto res.users, and _add_field() raises
    unless the storage field is an attribute on the class.
    """
    _name = "res.partner"
    _inherit = "res.partner"

    my_blob = fields.Encryption()
    secret_note = fields.Char(encrypt="my_blob")
    secret_code = fields.Char(encrypt="my_blob")


class EncryptSugar(models.Model):
    """``encrypt=True`` shorthand, which creates rec_encrypted implicitly."""
    _name = "enc.test.sugar"
    _description = "Sugar Encryption Test"
    _inherit = ["enc.test.blob.inspector"]

    _blob_field = "rec_encrypted"

    name = fields.Char()
    secret_one = fields.Char(encrypt=True)
    secret_two = fields.Char(encrypt=True)


class EncryptGroup(models.Model):
    """Parent of an _inherits pair, with a custom named blob.

    This mirrors the shape used in production (eyrie.deployment.group, whose
    encrypt fields name their own blob) and is the case that breaks first if
    the storage field stops being set on the registry class.
    """
    _name = "enc.test.group"
    _description = "Encryption Test Group"
    _inherit = ["enc.test.blob.inspector"]

    _blob_field = "group_blob"

    name = fields.Char()
    group_secret = fields.Char(encrypt="group_blob")
    group_token = fields.Char(encrypt="group_blob")


class EncryptMember(models.Model):
    """Child that delegates to the group, so it inherits the encrypt fields."""
    _name = "enc.test.member"
    _description = "Encryption Test Member"
    _inherits = {"enc.test.group": "group_id"}

    group_id = fields.Many2one(
        "enc.test.group", required=True, ondelete="cascade",
    )
    label = fields.Char()
    # the blob lives on the parent table, so the inspector is read through it
    blob_key_version = fields.Integer(
        related="group_id.blob_key_version", string="Stored Key Version")
    keyring_current = fields.Integer(
        related="group_id.keyring_current", string="Current Key Version")
    blob_is_pending = fields.Boolean(
        related="group_id.blob_is_pending", string="Pending Re-encryption")
