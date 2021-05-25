from odoo import fields
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger("__name__")

def ca_cpp_canada_pension_plan_withholding(payslip, categories):
    #K2 = [(0.15 × ((0.0545 × ((S1 × PI) + B1 – $3,500)*, maximum $3,166.45)))) + (0.15 × ((0.0158 × ((S1 × IE) + B1), maximum $889.54))]

    payperiods_s1 = _compute_payperiod_ratio_s1(payslip)
    pensionable_income_pi = _compute_pensionable_income_pi(payslip, categories)
    #todo: remove
    import pydevd_pycharm
    pydevd_pycharm.settrace('192.168.1.27', port=6900, stdoutToServer=True, stderrToServer=True)

    return 0.0, 0.0

def _compute_payperiod_ratio_s1(payslip):
    wage_type = payslip.wage_type
    pay_periods = payslip.dict.PAY_PERIODS_IN_YEAR[wage_type]
    if wage_type == 'annually':
        return 1
    elif wage_type == 'semi_annually':
        if payslip.date_to.month < 7:
            return 1/pay_periods
        else:
            return 2/pay_periods
    elif wage_type == 'quarterly':
        quarters = {
            1:1,
            2:1,
            3:1,
            4:2,
            5:2,
            6:2,
            7:3,
            8:3,
            9:3,
            10:4,
            11:4,
            12:4,
        }
        quarter = quarters[payslip.date_to.month]
        return quarter/pay_periods
    elif wage_type == 'bi-monthly':
        bi_monthly_int = {
            1:1,
            2:1,
            3:2,
            4:2,
            5:3,
            6:3,
            7:4,
            8:4,
            9:5,
            10:5,
            11:6,
            12:6,
        }
        bi_monthly = bi_monthly_int[payslip.date_to.month]
        return bi_monthly/pay_periods
    elif wage_type == 'monthly':
        return payslip.date_to.month/pay_periods
    elif wage_type == 'semi-monthly':
        pay_period = payslip.date_to.month * 2
        if payslip.date_to.day <= 15:
            return pay_period/pay_periods
        else:
            pay_period += 1
            return pay_period/pay_periods
    elif wage_type == 'bi-weekly':
        week_num = payslip.date_to.isocalendar()[1]
        if week_num == 53:
            return 1
        else:
            return week_num/pay_periods
    elif wage_type == 'weekly':
        return payslip.date_to.isocalendar()[1]/pay_periods
    elif wage_type == 'daily':
        day_of_year = payslip.date_to.timetuple().tm_yday
        return day_of_year/pay_periods
    else:
        raise Exception(f'Payslip does not have a valid wage_type.  The wagetype presented is "{wage_type}".')

def _compute_pensionable_income_of_slip(slip):
    pensionable_income = 0.0
    for line in slip.line_ids:
        if line.category_id.code == 'BASIC':
            pensionable_income += line.amount
    return pensionable_income

def _compute_pensionable_income_year_to_date_piytd(payslip, categories):
    employee_payslips = payslip.dict.env['hr.payslip'].search([
        ('employee_id', '=', payslip.dict.employee_id.id),
        ('id', '!=', payslip.dict.id),
    ])
    piytd = 0.0
    for slip in employee_payslips:
        piytd += _compute_pensionable_income_of_slip(slip)
    return piytd

def _compute_pensionable_income_pi(payslip, categories):
    """
    PI = Pensionable income for the pay period, or the gross income plus any taxable benefits for the pay period, plus PIYTD
    """
    pensionable_income_year_to_date_piytd = _compute_pensionable_income_year_to_date_piytd(payslip, categories)
    pensionable_income_for_current_payslip = _compute_pensionable_income_of_slip(payslip)
    return pensionable_income_year_to_date_piytd + pensionable_income_for_current_payslip





