# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

import requests
import json
from datetime import datetime as dt
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SignifydCase(models.Model):
    _name = 'signifyd.case'
    _description = 'Stores Signifyd case information on orders.'

    connector_id = fields.Many2one('signifyd.connector', string='Signifyd Connector')
    order_id = fields.Many2one('sale.order', required=True)
    partner_id = fields.Many2one('res.partner')
    case_id = fields.Char(string='Case ID')
    ref = fields.Char(string='Reference', help="Signifyd Order ID, set to the sale order's name for new cases. Previously Unique ID.")
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
    coverage_ids = fields.Many2many('signifyd.coverage', string='Coverage', help='Accepted Coverage Types')
    coverage_line_ids = fields.One2many('signifyd.case.coverage', 'case_id')

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

    def get_decision_vals(self, data=None):
        self.ensure_one()

        if not data:
            api = self.connector_id.get_connection()
            response = api.get_decision(self.ref)
            response.raise_for_status()
            data = response.json()

        decision = data['decision']
        case_vals = {
            'last_update': decision.get('createdAt'),
            'checkpoint_action': decision.get('checkpointAction'),
            'score': decision.get('score'),
            'coverage_line_ids': []
        }

        coverage = data.get('coverage')
        if coverage:
            coverage_map = {
                'inrChargebacks': self.env.ref('website_sale_signifyd.signifyd_coverage_inr').id,
                'fraudChargebacks': self.env.ref('website_sale_signifyd.signifyd_coverage_fraud').id,
                'snadChargebacks': self.env.ref('website_sale_signifyd.signifyd_coverage_snad').id,
                'allChargebacks': self.env.ref('website_sale_signifyd.signifyd_coverage_all').id
            }
            for name, vals in coverage.items():
                if not vals:
                    continue
                case_vals['coverage_line_ids'] += [(0, 0, {
                    'coverage_type_id': coverage_map[name],
                    'amount': vals.get('amount'),
                    'currency_id': self.env['res.currency'].search(
                        [('name', '=ilike', vals.get('currency'))], limit=1).id,
                })]

        return {k: v for k, v in case_vals.items() if v}

    def action_force_update_case(self):
        for record in self:
            record.update_case_info()

    def update_case_info(self, data=None):
        self.ensure_one()
        if not self.case_id:
            raise UserError(_('Case not represented in Signifyd.'))

        vals = self.get_decision_vals(data)

        outcome = vals.get('guarantee_disposition')
        checkpoint_action = vals.get('checkpoint_action')
        if outcome == 'DECLINED' or checkpoint_action == 'REJECT':
            connector = self._get_connector()
            for user in connector.notify_user_ids:
                self.create_notification(user, outcome or checkpoint_action)

        self.sudo().write(vals)

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
