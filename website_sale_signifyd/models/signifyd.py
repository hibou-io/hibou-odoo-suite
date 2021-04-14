import requests
import json
from datetime import datetime as dt
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SignifydCase(models.Model):
    _name = 'signifyd.case'
    _description = 'Stores Signifyd case information on orders.'

    order_id = fields.Many2one('sale.order')
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
    guarantee_eligible = fields.Boolean('Eligible for Guarantee')
    guarantee_requested = fields.Boolean('Requested Guarantee')
    score = fields.Float(string='Transaction Score')
    adjusted_score = fields.Float(string='Adjusted Score')
    signifyd_url = fields.Char('Signifyd.com', compute='_compute_signifyd_url')

    @api.model
    def _compute_signifyd_url(self):
        for record in self:
            if record.case_id:
                self.signifyd_url = 'https://app.signifyd.com/cases/%s' % record.case_id
            else:
                self.signifyd_url = ''

    def write(self, vals):
        res = super(SignifydCase, self).write(vals)
        disposition = vals.get('guarantee_disposition')
        if disposition:
            self.order_id.message_post(body=_('Signifyd Updated Record to %s' % vals['guarantee_disposition']),
                                       subtype='gcl_signifyd_connector.disposition_change')
        return res

    @api.model
    def post_case(self, values):
        signifyd = self.env['signifyd.connector']
        headers = signifyd.get_headers()
        data = json.dumps(values, indent=4, sort_keys=True, default=str)

        r = requests.post(
            signifyd.API_URL + '/cases',
            headers=headers,
            data=data,
        )
        return r.json()

    @api.model
    def get_case(self):
        signifyd = self.env['signifyd.connector']
        headers = signifyd.get_headers()
        r = requests.get(
            signifyd.API_URL + '/cases/' + str(self.case_id),
            headers=headers
        )
        return r.json()

    @api.model
    def request_guarantee(self, *args):
        signifyd = self.env['signifyd.connector']
        headers = signifyd.get_headers()
        values = json.dumps({"caseId": self.case_id})
        r = requests.post(
            signifyd.API_URL + '/async/guarantees',
            headers=headers,
            data=values,
        )

        if 200 <= r.status_code < 300:
            self.write({'guarantee_requested': True})
        else:
            msg = r.content.decode("utf-8")
            raise UserError(_(msg))

    def action_request_guarantee(self):
        for record in self:
            record.request_guarantee()

    def action_force_update_case(self):
        for record in self:
            record.update_case_info()

    @api.model
    def update_case_info(self, vals=None):
        if not vals:
            case = self.get_case()
            case_id = case.get('caseId')
            team_id = case.get('teamId')
            team_name = case.get('teamName')
            uuid = case.get('uuid')
            status = case.get('status')
            review_disposition = case.get('reviewDisposition')
            order_outcome = case.get('orderOutcome')
            guarantee_disposition = case.get('guaranteeDisposition')
            adjusted_score = case.get('adjustedScore')
            score = case.get('score')
            guarantee_eligible = case.get('guaranteeEligible')
            # order_id = case.get('orderId')

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
                'guarantee_eligible': guarantee_eligible,
                'last_update': dt.now(),
            }

        outcome = vals.get('guarantee_disposition')
        if outcome == 'DECLINED':
            for user in self.env.company.signifyd_connector_id.notify_user_ids:
                self.create_notification(user, outcome)

        self.write(vals)

    def create_notification(self, user, outcome):
        self.ensure_one()
        vals = {
            'summary': 'Signifyd Case %s %s' % (self.case_id, outcome),
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'user_id': user.id,
            'res_id': self.order_id.id,
            'res_model_id': self.env['ir.model']._get('sale.order').id,
        }
        self.env['mail.activity'].create(vals)
