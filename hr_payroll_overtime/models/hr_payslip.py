from collections import defaultdict
from odoo import models


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def aggregate_overtime(self, work_data, day_week_start=None):
        """

        :param work_data: list(tuple(iso_date, list(tuple(hr.work.entry.type(), hours, original_record))
        :param day_week_start: day of the week to start (otherwise employee's resource calendar start day of week)
        :return: dict(hr.work.entry.type(): list(days_worked, hours_worked, ))
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
        for iso_date, entries in work_data:
            iso_date = _adjust_week(iso_date)
            for work_type, hours, _ in entries:
                self._aggregate_overtime_add_work_type_hours(work_type, hours, iso_date, result, iso_days, day_hours, week_hours)

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
        week = iso_date[1]
        if work_type.overtime_work_type_id and work_type.overtime_type_id:
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
                # we need to save this because it won't be set once it reenter, we won't know what the original
                # overtime multiplier was
                working_aggregation[work_type.overtime_work_type_id][2] = work_type.overtime_type_id.multiplier
                self._aggregate_overtime_add_work_type_hours(work_type.overtime_work_type_id, ot_hours, iso_date,
                                                             working_aggregation, iso_days, day_hours, week_hours)
        else:
            # No overtime, just needs added to set
            if iso_date not in iso_days:
                iso_days.add(iso_date)
                working_aggregation[work_type][0] += 1.0
            working_aggregation[work_type][1] += hours
            day_hours[iso_date] += hours
            week_hours[week] += hours
