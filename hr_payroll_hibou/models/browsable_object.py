# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import fields
from odoo.addons.hr_payroll.models import browsable_object


class BrowsableObject(object):
    def __init__(self, employee_id, dict, env):
        self.employee_id = employee_id
        self.dict = dict
        self.env = env
        # Customization to allow changing the behavior of the discrete browsable objects.
        # you can think of this as 'compiling' the query based on the configuration.
        sum_field = env['ir.config_parameter'].sudo().get_param('hr_payroll.payslip.sum_behavior', 'date_from')
        if sum_field == 'date' and 'date' not in env['hr.payslip']:
            # missing attribute, closest by definition
            sum_field = 'date_to'
        if not sum_field:
            sum_field = 'date_from'
        self._compile_browsable_query(sum_field)

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0

    def __getitem__(self, key):
        return self.dict[key] or 0.0

    def _compile_browsable_query(self, sum_field):
        pass


class InputLine(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""
    def _compile_browsable_query(self, sum_field):
        self.__browsable_query = """
            SELECT sum(amount) as sum
            FROM hr_payslip as hp, hr_payslip_input as pi
            WHERE hp.employee_id = %s AND hp.state in ('done', 'paid')
            AND hp.{sum_field} >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""".format(sum_field=sum_field)

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(self.__browsable_query, (self.employee_id, from_date, to_date, code))
        return self.env.cr.fetchone()[0] or 0.0


class WorkedDays(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""
    def _compile_browsable_query(self, sum_field):
        self.__browsable_query = """
            SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
            FROM hr_payslip as hp, hr_payslip_worked_days as pi
            WHERE hp.employee_id = %s AND hp.state in ('done', 'paid')
            AND hp.{sum_field} >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""".format(sum_field=sum_field)

    def _sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(self.__browsable_query, (self.employee_id, from_date, to_date, code))
        return self.env.cr.fetchone()

    def sum(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[0] or 0.0

    def sum_hours(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[1] or 0.0


class Payslips(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""
    def _compile_browsable_query(self, sum_field):
        # Note that the core odoo has this as `hp.credit_note = False` but what if it is NULL?
        # reverse of the desired behavior.
        self.__browsable_query_rule = """
            SELECT sum(case when hp.credit_note is not True then (pl.total) else (-pl.total) end)
            FROM hr_payslip as hp, hr_payslip_line as pl
            WHERE hp.employee_id = %s AND hp.state in ('done', 'paid')
            AND hp.{sum_field} >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""".format(sum_field=sum_field)
        # Original (non-recursive)
        # self.__browsable_query_category = """
        #     SELECT sum(case when hp.credit_note is not True then (pl.total) else (-pl.total) end)
        #     FROM hr_payslip as hp, hr_payslip_line as pl, hr_salary_rule_category as rc
        #     WHERE hp.employee_id = %s AND hp.state = 'done'
        #     AND hp.{sum_field} >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
        #     AND rc.id = pl.category_id AND rc.code = %s""".format(sum_field=sum_field)

        # Hibou Recursive version
        self.__browsable_query_category = """
            WITH RECURSIVE
            category_by_code as (
                SELECT id
                FROM hr_salary_rule_category
                WHERE code = %s
                ),
            category_ids as (
                SELECT COALESCE((SELECT id FROM category_by_code), -1) AS id
                UNION ALL
                SELECT rc.id
                FROM hr_salary_rule_category AS rc
                JOIN category_ids AS rcs ON rcs.id = rc.parent_id
            )

            SELECT sum(case when hp.credit_note is not True then (pl.total) else (-pl.total) end)
            FROM hr_payslip as hp, hr_payslip_line as pl
            WHERE hp.employee_id = %s AND hp.state in ('done', 'paid')
            AND hp.{sum_field} >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id
            AND pl.category_id in (SELECT id from category_ids)""".format(sum_field=sum_field)

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(self.__browsable_query_rule, (self.employee_id, from_date, to_date, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def rule_parameter(self, code):
        return self.env['hr.rule.parameter']._get_parameter_from_code(code, self.dict.date_to)

    def sum_category(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()

        self.env['hr.payslip'].flush(['credit_note', 'employee_id', 'state', 'date_from', 'date_to'])
        self.env['hr.payslip.line'].flush(['total', 'slip_id', 'category_id'])
        self.env['hr.salary.rule.category'].flush(['code'])

        # standard version
        # self.env.cr.execute(self.__browsable_query_category, (self.employee_id, from_date, to_date, code))
        # recursive category version
        self.env.cr.execute(self.__browsable_query_category, (code, self.employee_id, from_date, to_date))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    @property
    def paid_amount(self):
        return self.dict._get_paid_amount()

    # Hibou helper
    @property
    def pay_periods_in_year(self):
        return self.dict.get_pay_periods_in_year()

# Patch over Core
browsable_object.BrowsableObject.__init__ = BrowsableObject.__init__
browsable_object.BrowsableObject._compile_browsable_query = BrowsableObject._compile_browsable_query
browsable_object.InputLine._compile_browsable_query = InputLine._compile_browsable_query
browsable_object.InputLine.sum = InputLine.sum
browsable_object.WorkedDays._compile_browsable_query = WorkedDays._compile_browsable_query
browsable_object.WorkedDays.sum = WorkedDays.sum
browsable_object.Payslips._compile_browsable_query = Payslips._compile_browsable_query
browsable_object.Payslips.sum = Payslips.sum
browsable_object.Payslips.sum_category = Payslips.sum_category
browsable_object.Payslips.pay_periods_in_year = Payslips.pay_periods_in_year
