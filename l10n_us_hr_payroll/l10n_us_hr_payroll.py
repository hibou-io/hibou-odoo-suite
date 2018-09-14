from odoo import models, fields, api


class USHrContract(models.Model):
    FUTA_TYPE_EXEMPT = 'exempt'
    FUTA_TYPE_BASIC = 'basic'
    FUTA_TYPE_NORMAL = 'normal'
    FUTA_YEARS_VALID = (
        2016,
        2017,
        2018,
    )

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

    fica_exempt = fields.Boolean(string='FICA Exempt', help="Exempt from Social Security and "
                                                            "Medicare e.g. F1 Student Visa")
    futa_type = fields.Selection([
        (FUTA_TYPE_EXEMPT, 'Exempt (0%)'),
        (FUTA_TYPE_NORMAL, 'Normal Net Rate (0.6%)'),
        (FUTA_TYPE_BASIC, 'Basic Rate (6%)'),
    ], string="Federal Unemployment Tax Type (FUTA)", default='normal')

    @api.multi
    def futa_rate(self, year):
        self.ensure_one()

        if year not in self.FUTA_YEARS_VALID:
            raise NotImplemented('FUTA rate for Year: ' + str(year) + ' not known.')

        if self.futa_type == self.FUTA_TYPE_EXEMPT:
            return 0.0
        elif self.futa_type == self.FUTA_TYPE_NORMAL:
            return 0.6
        else:
            return 6.0
