from odoo import models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def ytd(self, code, allow_draft=False):
        to_date = self.date_to
        from_date = self.date_to[:4] + '-01-01'
        state_allowed = ('done', 'verify') if not allow_draft else ('done', 'verify', 'draft')
        self.env.cr.execute("""
            SELECT sum(total) as sum
            FROM hr_payslip as hp
            JOIN hr_payslip_line as pi ON hp.id = pi.slip_id
            WHERE hp.employee_id = %s 
                  AND hp.state in %s
                  AND hp.date_to >= %s AND hp.date_to <= %s AND pi.code = %s""",
                            (self.employee_id.id, state_allowed, from_date, to_date, code))
        return self.env.cr.fetchone()[0] or 0.0
