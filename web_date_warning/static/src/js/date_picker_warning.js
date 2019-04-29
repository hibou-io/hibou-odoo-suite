odoo.define('web.datepicker.warn', function (require) {
"use strict";

var basicFields = require('web.basic_fields');
var fieldRegistry = require('web.field_registry');

var _setValue = function(value) {
    this._super(value);
    if (this.attrs.options.warn_future || this.attrs.options.warn_past) {
        var now = moment();
        var val = moment(value);
        var ms_diff = val - now;
        var warning = false;
        var days = Math.ceil(ms_diff / 1000 / (24 * 3600));
        if (days >= this.attrs.options.warn_future) {
            warning = days + ' days in the future!';
        } else if (-days >= this.attrs.options.warn_past) {
            warning = -days + ' days in the past!';
        }
        if (!warning) {
            this.$el.find('.o_date_warning').remove();
        } else {
            if (this.$el.find('.o_date_warning').length) {
                this.$el.find('.o_date_warning').text(warning);
            } else {
                this.$el.append('<p class="o_date_warning text-danger">' + warning + '</p>');
            }
        }
    }
}

var FieldDateWarn = basicFields.FieldDate.extend({
    _setValue: _setValue,
});

var FieldDateTimeWarn = basicFields.FieldDateTime.extend({
    _setValue: _setValue,
});

fieldRegistry.add('date-warn', FieldDateWarn);
fieldRegistry.add('datetime-warn', FieldDateTimeWarn);

});
