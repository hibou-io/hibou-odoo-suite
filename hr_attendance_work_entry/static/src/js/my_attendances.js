odoo.define('hr_attendance_work_entry.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var MyAttendances = require('hr_attendance.my_attendances');

var MyTypedAttendances = MyAttendances.extend({
    events: _.extend({}, MyAttendances.prototype.events, {
        "click .o_hr_attendance_punch_type": _.debounce(function(e) {
            var work_entry_type = $(e.target).data('work-entry-type');
            this.update_attendance(work_entry_type);
        }, 200, true),
    }),

    willStart: function () {
        var self = this;

        var def = this._rpc({
                model: 'hr.attendance',
                method: 'gather_attendance_work_types',
                args: []})
            .then(function (res) {
                self.work_types = res;
            });

        return Promise.all([def, this._super.apply(this, arguments)]);
    },

    update_attendance: function (type) {
        var self = this;
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', false, type],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
});

core.action_registry.add('hr_attendance_my_attendances', MyTypedAttendances);

return MyTypedAttendances;

});