from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_worked_day_lines_values(self, domain=None):
        worked_day_lines_values = super()._get_worked_day_lines_values(domain=domain)
        return self._process_worked_day_lines_values(worked_day_lines_values, domaian=domain)

    def _process_worked_day_lines_values(self, worked_day_lines_values, domaian=None):
        if not self.state in ('draft', 'verify'):
            return worked_day_lines_values

        worked_day_lines_values = self._filter_worked_day_lines_values(worked_day_lines_values)
        work_data = self._pre_aggregate_work_data()
        work_data = self._post_aggregate_work_data(work_data)
        processed_data = self._aggregate_overtime(work_data)
        worked_day_lines_values += [{
            'number_of_days': data[0],
            'number_of_hours': data[1],
            'rate': data[2],
            'contract_id': self.contract_id.id,
            'work_entry_type_id': work_type.id,
        } for work_type, data in processed_data.items()]
        return worked_day_lines_values

    def _filter_worked_day_lines_values(self, worked_day_lines_values):
        # e.g. maybe you want to remove the stock 'WORK100' lines
        # returns new worked_day_lines_values
        return worked_day_lines_values

    def _pre_aggregate_work_data(self):
        # returns dict(iso_date: list(tuple(hr.work.entry.type(), hours, original_record))
        return defaultdict(list)

    def _post_aggregate_work_data(self, work_data):
        # takes pre_aggregate data format and converts it.
        # this is to simplify algorithm and guarantee ordered by iso_date semantics
        # work_data: dict(iso_date: list(tuple(hr.work.entry.type(), hours, original_record))
        # returns: list(tuple(iso_date, list(tuple(hr.work.entry.type(), hours, original_record))
        return [(iso_date, work_data[iso_date]) for iso_date in sorted(work_data.keys())]

    def _aggregate_overtime(self, work_data, day_week_start=None):
        """

        :param work_data: list(tuple(iso_date, list(tuple(hr.work.entry.type(), hours, original_record))
        :param day_week_start: day of the week to start (otherwise employee's resource calendar start day of week)
        :return: dict(hr.work.entry.type(): list(days_worked, hours_worked, rate))
        """
        if not day_week_start:
            if self.employee_id.resource_calendar_id.day_week_start:
                day_week_start = self.employee_id.resource_calendar_id.day_week_start
            else:
                day_week_start = '1'
        day_week_start = int(day_week_start)
        if day_week_start < 1 or day_week_start > 7:
            day_week_start = 1

        def _adjust_week(isodate):
            if isodate[2] < day_week_start:
                return (isodate[0], isodate[1] + 1, isodate[2])
            return isodate

        result = defaultdict(lambda: [0.0, 0.0, 1.0])
        day_hours = defaultdict(float)
        week_hours = defaultdict(float)
        iso_days = set()
        try:
            for iso_date, entries in work_data:
                iso_date = _adjust_week(iso_date)
                for work_type, hours, _ in entries:
                    self._aggregate_overtime_add_work_type_hours(work_type, hours, iso_date, result, iso_days, day_hours, week_hours)
        except RecursionError:
            raise UserError(_('RecursionError raised.  Ensure you have not overtime loops, you should have an '
                            'end work type that does not have any "overtime" version, and would be considered '
                            'the "highest overtime" work type and rate.'))

        return result

    def _aggregate_overtime_add_work_type_hours(self, work_type, hours, iso_date, working_aggregation, iso_days, day_hours, week_hours):
        """
        :param work_type: work type of hours being added
        :param hours: hours being added
        :param iso_date: date hours were worked
        :param working_aggregation: dict of work type hours as they are processed
        :param iso_days: set of iso days already seen
        :param day_hours: hours worked on iso dates already processed
        :param week_hours: hours worked on iso week already processed
        :return:
        """
        override = work_type.override_for_iso_date(iso_date)
        if override:
            new_work_type = override.work_type_id
            multiplier = override.multiplier
            if work_type == new_work_type:
                # trivial infinite recursion from override
                raise UserError(_('Work type "%s" (id %s) must not have itself as its override work type. '
                                'This occurred due to an override line "%s".', work_type.name, work_type.id, override.name))
            # update the work_type on this step.
            work_type = new_work_type
            working_aggregation[work_type][2] = multiplier

        week = iso_date[1]
        if not self.contract_id.is_overtime_exempt and work_type.overtime_work_type_id and work_type.overtime_type_id:
            ot_h_w = work_type.overtime_type_id.hours_per_week
            ot_h_d = work_type.overtime_type_id.hours_per_day

            regular_hours = hours
            # adjust the hours based on overtime conditions
            if ot_h_d and (day_hours[iso_date] + hours) > ot_h_d:
                # daily overtime in effect
                remaining_hours = max(ot_h_d - day_hours[iso_date], 0.0)
                regular_hours = min(remaining_hours, hours)
            elif ot_h_w:
                # not daily, but weekly limits....
                remaining_hours = max(ot_h_w - week_hours[week], 0.0)
                regular_hours = min(remaining_hours, hours)
            ot_hours = hours - regular_hours
            if regular_hours:
                if iso_date not in iso_days:
                    iso_days.add(iso_date)
                    working_aggregation[work_type][0] += 1.0
                working_aggregation[work_type][1] += regular_hours
                day_hours[iso_date] += regular_hours
                week_hours[week] += regular_hours
            if ot_hours:
                overtime_work_type = work_type.overtime_work_type_id
                multiplier = work_type.overtime_type_id.multiplier
                override = work_type.overtime_type_id.override_for_iso_date(iso_date)
                if work_type == overtime_work_type:
                    # trivial infinite recursion
                    raise UserError(_('Work type "%s" (id %s) must not have itself as its next overtime type.', work_type.name, work_type.id))
                if override:
                    overtime_work_type = override.work_type_id
                    multiplier = override.multiplier
                    if work_type == overtime_work_type:
                        # trivial infinite recursion from override
                        raise UserError(_('Work type "%s" (id %s) must not have itself as its next overtime type. '
                                        'This occurred due to an override "%s" from overtime rules "%s".', 
                            work_type.name, work_type.id, override.name, work_type.overtime_type_id.name))
                # we need to save this because it won't be set once it reenter, we won't know what the original
                # overtime multiplier was
                working_aggregation[overtime_work_type][2] = multiplier
                self._aggregate_overtime_add_work_type_hours(overtime_work_type, ot_hours, iso_date,
                                                             working_aggregation, iso_days, day_hours, week_hours)
        else:
            # No overtime, just needs added to set
            if iso_date not in iso_days:
                iso_days.add(iso_date)
                working_aggregation[work_type][0] += 1.0
            working_aggregation[work_type][1] += hours
            day_hours[iso_date] += hours
            week_hours[week] += hours


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    rate = fields.Float(string='Rate', default=1.0)

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'payslip_id.normal_wage', 'payslip_id.sum_worked_hours', 'rate')
    def _compute_amount(self):
        for worked_days in self:
            if not worked_days.contract_id:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id._get_contract_wage(work_type=worked_days.work_entry_type_id) * worked_days.number_of_hours * worked_days.rate if worked_days.is_paid else 0
            else:
                worked_days.amount = worked_days.payslip_id.normal_wage * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
