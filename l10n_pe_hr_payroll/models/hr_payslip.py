# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import date

from odoo import api, fields, models
from .rules.general import _general_rate
from .rules.ir_4ta_cat import ir_4ta_cat
from .rules.ir_5ta_cat import ir_5ta_cat


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model_create_multi
    def create(self, vals_list):
        payslips = super().create(vals_list)
        draft_slips = payslips.filtered(lambda p: p.employee_id and p.state == 'draft')
        if not draft_slips:
            return payslips
        
        for slip in draft_slips.filtered(lambda s: s.struct_id.code == 'PE5GRATIF'):
            slip._pe_5thcat_gratif_update_input_line()
        
        return payslips
    
    def _pe_5thcat_gratif_update_input_line(self):
        full_months_type = self.env.ref('l10n_pe_hr_payroll.input_type_gratif_months', raise_if_not_found=False)
        if not full_months_type:
            return
        for payslip in self:
            # compute full months, for now I'll hard code to 6
            amount = payslip._pe_5thcat_gratif_months()
            lines_to_remove = payslip.input_line_ids.filtered(lambda x: x.input_type_id == full_months_type)
            input_lines_vals = [(2, line.id, False) for line in lines_to_remove]
            input_lines_vals.append((0, 0, {
                'amount': amount,
                'input_type_id': full_months_type.id
            }))
            payslip.update({'input_line_ids': input_lines_vals})
    
    def _pe_5thcat_gratif_months(self):
        full_months = 0
        # are we in July or December?
        # brute force, but this algorithm should be very very fast
        date_hire = self.contract_id.first_contract_date
        if self.date_to.month == 7:
            for i in range(1, 7):
                if date_hire < date(self.date_to.year, i, 15):
                    full_months += 1
        else:
            for i in range(7, 13):
                # note this is run in December, so it should look at current year
                if date_hire < date(self.date_to.year, i, 15):
                    full_months += 1
        return full_months

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'general_rate': _general_rate,
            'ir_4ta_cat': ir_4ta_cat,
            'ir_5ta_cat': ir_5ta_cat,
        })
        return res
    
    def _get_paid_amount(self):
        if self.struct_id.code == 'PE5GRATIF':
            return self._pe_5thcat_gratif()
        return super()._get_paid_amount()

    def _pe_5thcat_gratif(self):
        if self.contract_id.structure_type_id != self.struct_id.type_id:
            return 0.0
        
        # TODO hourly averages daily hours to compute from wage
        basic = self.contract_id._get_contract_wage()
        month_line = self.input_line_ids.filtered(lambda l: l.code == 'MONTHS')
        if not basic or not month_line:
            return 0.0
        # normalize to 6 months
        return basic * (1.0 / 6.0) * month_line.amount
