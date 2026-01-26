# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import http
from odoo.http import request, content_disposition

class WebWellKnown(http.Controller):
    @http.route('/.well-known/<path:path>', type='http', auth='public', methods=['GET'], csrf=False)
    def well_known_path(self, path, **kwargs):
        well_known_paths = request.env['well.known.path'].sudo()
        well_known_record = well_known_paths.search([('path', '=', path)], limit=1)
        
        if not well_known_record:
            return http.Response(status=404)  # Return a 404 Not Found if the path does not exist
        
        if well_known_record.file:
            text_content = well_known_record.file.decode('utf-8')

            return request.make_response(
                text_content,  # Decode binary content to a string
                headers=[('Content-Type', 'text/plain; charset=utf-8')]
            )
        
        
        return well_known_record.value or ''  # Return the value if no binary content is present, or empty string if value is None
