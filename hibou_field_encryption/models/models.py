from odoo import models, fields

ENCRYPTION_SUPPORTED_FIELD_TYPES = ["char", "text", "html", "selection"]


class Base(models.AbstractModel):
    _inherit = 'base'

    def _valid_field_parameter(self, field, name):
        return (name == 'encrypt' and field.type in ENCRYPTION_SUPPORTED_FIELD_TYPES) or super()._valid_field_parameter(field, name)


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    ttype = fields.Selection(selection_add=[('encryption', 'encryption')], ondelete={'encryption': 'cascade'})
