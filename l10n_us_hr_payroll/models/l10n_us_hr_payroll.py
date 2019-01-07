from openerp import models, fields, api


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def get_futa_rate(self, contract):
        self.ensure_one()
        if contract.futa_type == USHrContract.FUTA_TYPE_EXEMPT:
            rate = self.get_rate('US_FUTA_EXEMPT')
        elif contract.futa_type == USHrContract.FUTA_TYPE_NORMAL:
            rate = self.get_rate('US_FUTA_NORMAL')
        else:
            rate = self.get_rate('US_FUTA_BASIC')
        return rate


class USHrContract(models.Model):
    FUTA_TYPE_EXEMPT = 'exempt'
    FUTA_TYPE_BASIC = 'basic'
    FUTA_TYPE_NORMAL = 'normal'

    _inherit = 'hr.contract'

    schedule_pay = fields.Selection(selection_add=[('semi-monthly', 'Semi-monthly')])
    w4_allowances = fields.Integer(string='Federal W4 Allowances', default=0)
    w4_filing_status = fields.Selection([
        ('', 'Exempt'),
        ('single', 'Single'),
        ('married', 'Married'),
        ('married_as_single', 'Married but at Single Rate'),
    ], string='Federal W4 Filing Status', default='single')
    w4_is_nonresident_alien = fields.Boolean(string="Federal W4 Is Nonresident Alien", default=False)
    w4_additional_withholding = fields.Float(string="Federal W4 Additional Withholding", default=0.0)

    external_wages = fields.Float(string='External Existing Wages', default=0.0)

    futa_type = fields.Selection([
        (FUTA_TYPE_EXEMPT, 'Exempt (0%)'),
        (FUTA_TYPE_NORMAL, 'Normal Net Rate (0.6%)'),
        (FUTA_TYPE_BASIC, 'Basic Rate (6%)'),
    ], string="Federal Unemployment Tax Type (FUTA)", default='normal')
