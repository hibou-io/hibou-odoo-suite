# Copyright 2020 Hibou Corp.
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import io
import base64
import logging
from minio import Minio
from minio.error import NoSuchKey

from odoo import api, exceptions, models, tools
from ..s3uri import S3Uri

_logger = logging.getLogger(__name__)


class MinioAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _get_minio_client(self):
        config = tools.config
        params = self.env['ir.config_parameter'].sudo()
        host = params.get_param('ir_attachment.location.host') or config.get('attachment_minio_host')
        region = params.get_param('ir_attachment.location.region') or config.get('attachment_minio_region', 'us-west-1')
        access_key = params.get_param('ir_attachment.location.access_key') or config.get('attachment_minio_access_key')
        secret_key = params.get_param('ir_attachment.location.secret_key') or config.get('attachment_minio_secret_key')
        secure = params.get_param('ir_attachment.location.secure') or config.get('attachment_minio_secure')
        if not all((host, access_key, secret_key)):
            raise exceptions.UserError('Incorrect configuration of attachment_minio.')
        return Minio(host,
                           access_key=access_key,
                           secret_key=secret_key,
                           region=region,
                           secure=bool(secure))

    @api.model
    def _get_minio_bucket(self, client, name=None):
        config = tools.config
        params = self.env['ir.config_parameter'].sudo()
        bucket = name or params.get_param('ir_attachment.location.bucket') or config.get('attachment_minio_bucket')
        if not bucket:
            raise exceptions.UserError('Incorrect configuration of attachment_minio -- Missing bucket.')
        if not client.bucket_exists(bucket):
            region = params.get_param('ir_attachment.location.region', 'us-west-1')
            client.make_bucket(bucket, region)
        return bucket

    @api.model
    def _get_minio_key(self, sha):
        # scatter files across 256 dirs
        # This mirrors Odoo's own object storage so that it is easier to migrate
        # to or from external storage.
        fname = sha[:2] + '/' + sha
        return fname

    @api.model
    def _get_minio_fname(self, bucket, key):
        return 's3://%s/%s' % (bucket, key)

    # core API methods from base_attachment_object_storage

    def _get_stores(self):
        res = super(MinioAttachment, self)._get_stores()
        res.append('s3')
        return res

    @api.model
    def _store_file_read(self, fname, bin_size=False):
        if fname.startswith('s3://'):
            client = self._get_minio_client()
            s3uri = S3Uri(fname)
            bucket = self._get_minio_bucket(client, name=s3uri.bucket())
            try:
                response = client.get_object(bucket, s3uri.item())
                return base64.b64encode(response.read())
            except NoSuchKey:
                _logger.info('attachment "%s" missing from remote object storage', (fname, ))
            return ''
        return super(MinioAttachment, self)._store_file_read(fname, bin_size=bin_size)

    @api.model
    def _store_file_write(self, key, bin_data):
        if self._storage() == 's3':
            client = self._get_minio_client()
            bucket = self._get_minio_bucket(client)
            minio_key = self._get_minio_key(key)
            with io.BytesIO(bin_data) as bin_data_io:
                client.put_object(bucket, minio_key, bin_data_io, len(bin_data),
                                  content_type=self.mimetype)
            return self._get_minio_fname(bucket, minio_key)
        return super(MinioAttachment, self)._store_file_write(key, bin_data)

    @api.model
    def _store_file_delete(self, fname):
        if fname.startswith('s3://'):
            client = self._get_minio_client()
            try:
                s3uri = S3Uri(fname)
            except ValueError:
                # Cannot delete unparsable file
                return True
            bucket_name = s3uri.bucket()
            if bucket_name == self._get_minio_bucket(client):
                try:
                    client.remove_object(bucket_name, s3uri.item())
                except NoSuchKey:
                    _logger.info('unable to remove missing attachment "%s" from remote object storage', (fname, ))
            else:
                _logger.info('skip delete "%s" because of bucket-mismatch', (fname, ))
            return
        return super(MinioAttachment, self)._store_file_delete(fname)
