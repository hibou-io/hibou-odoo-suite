from functools import partial
from datetime import timedelta
from odoo import api, models
from odoo.addons.resource.models.resource import make_aware


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def plan_days_end(self, days, day_dt, compute_leaves=False, domain=None):
        """
        Override to `plan_days` that allows you to get the nearest 'end' including today.
        """
        day_dt, revert = make_aware(day_dt)

        # which method to use for retrieving intervals
        if compute_leaves:
            get_intervals = partial(self._work_intervals, domain=domain)
        else:
            get_intervals = self._attendance_intervals

        if days >= 0:
            found = set()
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt + delta * n
                for start, stop, meta in get_intervals(dt, dt + delta):
                    found.add(start.date())
                    if len(found) >= days:
                        return revert(stop)
            return False

        elif days < 0:
            days = abs(days)
            found = set()
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt - delta * n
                for start, stop, meta in reversed(get_intervals(dt - delta, dt)):
                    found.add(start.date())
                    if len(found) == days:
                        return revert(start)
            return False

        else:
            return revert(day_dt)
