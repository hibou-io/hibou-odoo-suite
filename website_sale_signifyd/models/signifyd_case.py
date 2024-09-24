# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import requests
import json
from datetime import datetime as dt
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SignifydCase(models.Model):
    _name = 'signifyd.case'
    _description = 'Stores Signifyd case information on orders.'

    # flow_type = fields.Selection([('pre', 'PreAuth'), ('post', 'PostAuth')], default='post', required=True)

    order_id = fields.Many2one('sale.order', required=True)
    partner_id = fields.Many2one('res.partner')
    case_id = fields.Char(string='Case ID')
    uuid = fields.Char(string='Unique ID')
    status = fields.Selection([
        ('OPEN', 'Open'),
        ('DISMISSED', 'Dismissed'),
    ], string='Case Status')

    name = fields.Char(string='Headline')
    team_name = fields.Char(string='Team Name')
    team_id = fields.Char(string='Team ID')
    last_update = fields.Date('Last Update')

    review_disposition = fields.Selection([
        ('UNSET', 'Pending'),
        ('FRAUD', 'Fraudulent'),
        ('GOOD', 'Good'),
    ], string='Review Status')

    order_outcome = fields.Selection([
        ('PENDING', 'pending'),
        ('SUCCESSFUL', 'Successful'),
    ])

    guarantee_disposition = fields.Selection([
        ('IN_REVIEW', 'Reviewing'),
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined'),
        ('CANCELED', 'Canceled'),
    ], string='Guarantee Status')
    disposition_reason = fields.Char('Disposition Reason')
    score = fields.Float(string='Transaction Score')
    adjusted_score = fields.Float(string='Adjusted Score')
    signifyd_url = fields.Char('Signifyd.com', compute='_compute_signifyd_url')
    checkpoint_action = fields.Selection([
        ('ACCEPT', 'Accept'),
        ('HOLD', 'Hold'),
        ('REJECT', 'Reject'),
    ], string='Checkpoint Action')

    coverage_ids = fields.Many2many('signifyd.coverage', string='Requested Coverage Types')
    # TODO add to view

    def _get_connector(self):
        return self.order_id.website_id.signifyd_connector_id

    @api.model
    def _compute_signifyd_url(self):
        for record in self:
            if record.case_id:
                self.signifyd_url = 'https://app.signifyd.com/cases/%s' % (record.case_id, )
            else:
                self.signifyd_url = ''

    def write(self, vals):
        original_disposition = {c: c.guarantee_disposition for c in self}
        res = super(SignifydCase, self).write(vals)
        disposition = vals.get('guarantee_disposition', False)
        for case in self.filtered(lambda c: c.order_id and original_disposition[c] != disposition):
            case.order_id.message_post(body=_('Signifyd Updated Record to %s' % disposition),
                                       subtype_xmlid='website_sale_signifyd.disposition_change')
        return res

    @api.model
    def post_case(self, connector, values):
        headers = connector.get_headers()
        data = json.dumps(values, indent=4, sort_keys=True, default=str)

        # TODO this should be in `signifyd.connector`
        r = requests.post(
            connector.API_URL + '/cases',
            headers=headers,
            data=data,
        )
        return r.json()

    def get_case(self):
        self.ensure_one()
        if not self.case_id:
            raise UserError(_('Case not represented in Signifyd.'))
        connector = self._get_connector()
        headers = connector.get_headers()
        r = requests.get(
            connector.API_URL + '/cases/' + str(self.case_id),
            headers=headers
        )
        return r.json()

    def action_force_update_case(self):
        for record in self:
            record.update_case_info()

    def update_case_info(self, vals=None):
        self.ensure_one()
        if not self.case_id:
            raise UserError(_('Case not represented in Signifyd.'))
        if not vals:
            case = self.get_case()
            case_id = case.get('caseId')
            if not case_id:
                raise ValueError(_('Signifyd Case has no ID?'))
            team_id = case.get('teamId', self.team_id)
            team_name = case.get('teamName', self.team_name)
            uuid = case.get('uuid', self.uuid)
            status = case.get('status', self.status)
            review_disposition = case.get('reviewDisposition', self.review_disposition)
            order_outcome = case.get('orderOutcome', self.order_outcome)
            guarantee_disposition = case.get('guaranteeDisposition', self.guarantee_disposition)
            adjusted_score = case.get('adjustedScore', self.adjusted_score)
            score = case.get('score', self.score)
            checkpoint_action = case.get('checkpointAction', self.checkpoint_action)
            if not checkpoint_action and guarantee_disposition:
                if guarantee_disposition == 'APPROVED':
                    checkpoint_action = 'ACCEPT'
                elif guarantee_disposition == 'DECLINED':
                    checkpoint_action = 'REJECT'
                else:
                    checkpoint_action = 'HOLD'

            vals = {
                'case_id': case_id,
                'team_id': team_id,
                'team_name': team_name,
                'uuid': uuid,
                'status': status,
                'review_disposition': review_disposition,
                'order_outcome': order_outcome,
                'adjusted_score': adjusted_score,
                'guarantee_disposition': guarantee_disposition,
                'score': score,
                'last_update': dt.now(),  # why not just use
                'checkpoint_action': checkpoint_action,
            }

        outcome = vals.get('guarantee_disposition')
        checkpoint_action = vals.get('checkpoint_action')
        if outcome == 'DECLINED' or checkpoint_action == 'REJECT':
            connector = self._get_connector()
            for user in connector.notify_user_ids:
                self.create_notification(user, outcome or checkpoint_action)

        self.write(vals)

    def create_notification(self, user, outcome):
        self.ensure_one()
        vals = {
            'summary': 'Signifyd Case %s %s' % (self.case_id, outcome),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'user_id': user.id,
            'res_id': self.order_id.id,
            'res_model_id': self.env['ir.model']._get(self.order_id._name).id,
        }
        self.env['mail.activity'].create(vals)
