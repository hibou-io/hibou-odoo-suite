from odoo import models, fields


class USMTHrContract(models.Model):
    _inherit = 'hr.contract'

    mt_mw4_exemptions = fields.Integer(string='Montana MW-4 Exemptions', default=0,
                                       help='Box G')
    mt_mw4_additional_withholding = fields.Float(string="Montana MW-4 Additional Withholding", default=0.0,
                                                 help='Box H')
    mt_mw4_exempt = fields.Selection([
        ('', 'Not Exempt'),
        ('tribe', 'Registered Tribe'),
        ('reserve', 'Reserve or National Guard'),
        ('north_dakota', 'North Dakota'),
        ('montana_for_marriage', 'Montana for Marriage'),
    ], string='Exemption from Montana Withholding', default='', help='Section 2')
