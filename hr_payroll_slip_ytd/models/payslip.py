from odoo import models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def ytd(self, code, allow_draft=False):
        to_date = self.date_to
        from_date = str(self.date_to.year) + '-01-01'
        state_allowed = ('done', 'verify') if not allow_draft else ('done', 'verify', 'draft')
        self.env.cr.execute("""
            SELECT sum(total) as total,
                   sum(quantity) as quantity,
                   sum(amount) as amount
            FROM hr_payslip as hp
            JOIN hr_payslip_line as pi ON hp.id = pi.slip_id
            WHERE hp.employee_id = %s 
                  AND hp.state in %s
                  AND hp.date_to >= %s AND hp.date_to <= %s AND pi.code = %s""",
                            (self.employee_id.id, state_allowed, from_date, to_date, code))
        res = self.env.cr.dictfetchone()
        if res:
            # Can return dictionary with NULL aka Nones
            for key in res:
                res[key] = res[key] or 0.0
        else:
            res = {'total': 0.0, 'quantity': 0.0, 'amount': 0.0}
        return res
