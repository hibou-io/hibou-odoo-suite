odoo.define('hr_attendance_work_entry.kiosk_confirm', function (require) {
"use strict";

var core = require('web.core');
var KioskConfirm = require('hr_attendance.kiosk_confirm');
var KioskConfirmTyped = KioskConfirm.extend({
    events: _.extend({}, KioskConfirm.prototype.events, {
        "click .o_hr_attendance_punch_type": _.debounce(function(e) {
            var work_entry_type = $(e.target).data('work-entry-type');
            this.update_attendance(work_entry_type);
        }, 200, true),
        "click .o_hr_attendance_pin_pad_button_work": _.debounce(function(e) {
            var work_entry_type = $(e.target).data('work-entry-type');
            this.update_attendance_pin(work_entry_type);
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
                args: [[self.employee_id], this.next_action, false, type],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
    update_attendance_pin: function (type) {
        var self = this;
        this.$('.o_hr_attendance_pin_pad_button_ok').attr("disabled", "disabled");
        this.$('.o_hr_attendance_pin_pad_button_work').attr("disabled", "disabled");
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[this.employee_id], this.next_action, this.$('.o_hr_attendance_PINbox').val(), type],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                    self.$('.o_hr_attendance_PINbox').val('');
                    setTimeout( function() {
                        self.$('.o_hr_attendance_pin_pad_button_ok').removeAttr("disabled");
                        self.$('.o_hr_attendance_pin_pad_button_work').removeAttr("disabled");
                        }, 500);
                }
            });
    },
});

core.action_registry.add('hr_attendance_kiosk_confirm', KioskConfirmTyped);
return KioskConfirmTyped;
});