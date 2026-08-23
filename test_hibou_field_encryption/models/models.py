from odoo import fields, models


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
