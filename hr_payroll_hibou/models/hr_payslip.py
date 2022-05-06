# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields, models
from .browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # From IRS Publication 15-T or logically (annually, bi-monthly)
    PAY_PERIODS_IN_YEAR = {
        'annually':        1,
        'semi-annually':   2,
        'quarterly':       4,
        'bi-monthly':      6,
        'monthly':        12,
        'semi-monthly':   24,
        'bi-weekly':      26,
        'weekly':         52,
        'daily':         260,
    }

    def get_pay_periods_in_year(self):
        return self.PAY_PERIODS_IN_YEAR.get(self.contract_id.schedule_pay, 0)

    # We need to be able to support more complexity,
    # namely, that different employees will be paid by different wage types as 'salary' vs 'hourly'
    wage_type = fields.Selection(related='contract_id.wage_type')

    def get_year(self):
        """
        # Helper method to get the year (normalized between Odoo Versions)
        :return: int year of payslip
        """
        return self.date_to.year

    def _get_contract_wage(self, work_type=None):
        # Override if you pay differently for different work types
        # In 14.0, this utilizes new computed field mechanism,
        # but will still get the 'wage' field by default.

        # This would be a good place to override though with a 'work type'
        # based mechanism, like a minimum rate or 'rate card' implementation
        return self.contract_id._get_contract_wage(work_type=work_type)

    def _get_payslip_lines(self):
        # Override to inject current rule into local dictionary.
        # this allows checking for rules in sets or for 'set' rules on contracts.
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = localdict['categories'].dict.get(category.code, 0) + amount
            return localdict

        self.ensure_one()
        result = {}
        rules_dict = {}
        worked_days_dict = {line.code: line for line in self.worked_days_line_ids if line.code}
        inputs_dict = {line.code: line for line in self.input_line_ids if line.code}

        employee = self.employee_id
        contract = self.contract_id

        localdict = {
            **self._get_base_local_dict(),
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, rules_dict, self.env),
                'payslip': Payslips(employee.id, self, self.env),
                'worked_days': WorkedDays(employee.id, worked_days_dict, self.env),
                'inputs': InputLine(employee.id, inputs_dict, self.env),
                'employee': employee,
                'contract': contract
            }
        }
        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            localdict.update({
                'rule': rule,
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100})
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                #check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                #set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                # create/overwrite the rule in the temporary results
                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule.name,
                    'note': rule.note,
                    'salary_rule_id': rule.id,
                    'contract_id': contract.id,
                    'employee_id': employee.id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    'slip_id': self.id,
                }
        return result.values()
