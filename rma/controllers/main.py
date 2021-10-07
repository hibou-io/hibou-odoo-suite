# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import http, exceptions
from base64 import b64decode
import hmac
from hashlib import sha256
from datetime import datetime
from time import mktime


def create_hmac(secret, a_attchment_id, e_expires):
    return hmac.new(secret.encode(), str(str(a_attchment_id) + str(e_expires)).encode(), sha256).hexdigest()


def check_hmac(secret, hash_, a_attachment_id, e_expires):
    myh = hmac.new(secret.encode(), str(str(a_attachment_id) + str(e_expires)).encode(), sha256)
    return hmac.compare_digest(str(hash_), myh.hexdigest())


class RMAController(http.Controller):

    @http.route(['/rma_label'], type='http', auth='public', website=True)
    def index(self, *args, **request):
        a_attachment_id = request.get('a')
        e_expires = request.get('e')
        hash = request.get('h')

        if not all([a_attachment_id, e_expires, hash]):
            return http.Response('Invalid Request', status=400)

        now = datetime.utcnow()
        now = int(mktime(now.timetuple()))

        config = http.request.env['ir.config_parameter'].sudo()
        secret = str(config.search([('key', '=', 'database.secret')], limit=1).value)

        if not check_hmac(secret, hash, a_attachment_id, e_expires):
            return http.Response('Invalid Request', status=400)

        if now > int(e_expires):
            return http.Response('Expired', status=404)

        attachment = http.request.env['ir.attachment'].sudo().search([('id', '=', int(a_attachment_id))], limit=1)
        if attachment:
            data = attachment.datas
            filename = attachment.name
            mimetype = attachment.mimetype
            return http.request.make_response(b64decode(data), [
                ('Content-Type', mimetype),
                ('Content-Disposition', 'attachment; filename="' + filename + '"')])
        return http.Response('Invalid Attachment', status=404)
