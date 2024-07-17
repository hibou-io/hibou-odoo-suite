# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import mimetypes
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class WellKnownPath(models.Model):
    _name = 'well.known.path'
    _description = 'Well Known Path'

    path = fields.Char('Path', required=True, unique=True)
    value = fields.Text('Value')
    file = fields.Binary('Binary Content')
    filename = fields.Char('File Name')


    @api.onchange('file')
    def _onchange_file(self):
        for record in self:
            if record.file:
                if not record.filename:
                    record.filename = "well-known.txt"  # Set a default filename if none is provided
                if not record._is_text_file():
                    raise ValidationError("Only text files are allowed.")
    
    def _is_text_file(self):
        text_mime_types = [
            'text/plain',
        ]
        file_mimetype = mimetypes.guess_type(self.filename)[0]
        if file_mimetype in text_mime_types:
            return True
        return False

    @api.constrains('file', 'mimetype')
    def _check_text_file(self):
        for record in self:
            if record.file and not record._is_text_file():
                raise ValidationError("Only text files are allowed.")