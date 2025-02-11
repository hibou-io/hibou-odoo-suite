odoo.define('rma.submit', function (require) {
    'use strict';
    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var _t = core._t;

    publicWidget.registry.RmaSubmit = publicWidget.Widget.extend({
        selector: '.rma-form',
        events: {
            'click .rma-submit': '_onSubmit',
        },
  
        _onSubmit: function (e) {
            // Clear previous incorrect lines
            $('.border-danger').removeClass('border-danger text-danger');
            
            // Locate lines and notify user
            const incorrect_lines = $('.rma-qty').filter(function (idx, line) {
                const eligible = parseFloat(line.dataset?.qtyEligible || 0);
                const returned = parseFloat(line.value);
                return isNaN(returned) || eligible < returned || returned < 0;
            });
            if (incorrect_lines.length) {
                e.preventDefault();
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('Invalid quantity.'),
                    sticky: false,
                });
                incorrect_lines.addClass('text-danger border-danger');
            }
      }
    });
});
