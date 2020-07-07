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
            week = iso_date[1]
            for work_type, hours, _ in entries:
                if work_type.overtime_work_type_id and work_type.overtime_type_id:
                    ot_h_w = work_type.overtime_type_id.hours_per_week
                    ot_h_d = work_type.overtime_type_id.hours_per_day
                    if ot_h_d and (day_hours[iso_date] + hours) > ot_h_d:
                        if day_hours[iso_date] >= ot_h_d:
                            # no time is regular time
                            if iso_date not in iso_days:
                                iso_days.add(iso_date)
                                result[work_type.overtime_work_type_id][0] += 1.0
                            result[work_type.overtime_work_type_id][1] += hours
                            result[work_type.overtime_work_type_id][2] = work_type.overtime_type_id.multiplier
                        else:
                            remaining_regular_hours = ot_h_d - day_hours[iso_date]
                            if remaining_regular_hours - hours < 0.0:
                                # some time is regular time
                                regular_hours = remaining_regular_hours
                                overtime_hours = hours - remaining_regular_hours
                                if iso_date not in iso_days:
                                    iso_days.add(iso_date)
                                    result[work_type][0] += 1.0
                                result[work_type][1] += regular_hours
                                result[work_type.overtime_work_type_id][1] += overtime_hours
                                result[work_type.overtime_work_type_id][2] = work_type.overtime_type_id.multiplier
                            else:
                                # all time is regular time
                                if iso_date not in iso_days:
                                    iso_days.add(iso_date)
                                    result[work_type][0] += 1.0
                                result[work_type][1] += hours
                    elif ot_h_w:
                        if week_hours[week] > ot_h_w:
                            # no time is regular time
                            if iso_date not in iso_days:
                                iso_days.add(iso_date)
                                result[work_type.overtime_work_type_id][0] += 1.0
                            result[work_type.overtime_work_type_id][1] += hours
                            result[work_type.overtime_work_type_id][2] = work_type.overtime_type_id.multiplier
                        else:
                            remaining_regular_hours = ot_h_w - week_hours[week]
                            if remaining_regular_hours - hours < 0.0:
                                # some time is regular time
                                regular_hours = remaining_regular_hours
                                overtime_hours = hours - remaining_regular_hours
                                if iso_date not in iso_days:
                                    iso_days.add(iso_date)
                                    result[work_type][0] += 1.0
                                result[work_type][1] += regular_hours
                                result[work_type.overtime_work_type_id][1] += overtime_hours
                                result[work_type.overtime_work_type_id][2] = work_type.overtime_type_id.multiplier
                            else:
                                # all time is regular time
                                if iso_date not in iso_days:
                                    iso_days.add(iso_date)
                                    result[work_type][0] += 1.0
                                result[work_type][1] += hours
                    else:
                        # all time is regular time
                        if iso_date not in iso_days:
                            iso_days.add(iso_date)
                            result[work_type][0] += 1.0
                        result[work_type][1] += hours
                else:
                    if iso_date not in iso_days:
                        iso_days.add(iso_date)
                        result[work_type][0] += 1.0
                    result[work_type][1] += hours
                # Always
                day_hours[iso_date] += hours
                week_hours[week] += hours
        return result
