odoo.define('website_sale_payment_terms.payment_terms', function (require) {
    "use strict";

    require('web.dom_ready');
    var concurrency = require('web.concurrency');
    var core = require('web.core');
    var dp = new concurrency.DropPrevious();
    var publicWidget = require('web.public.widget');
    require('website_sale_delivery.checkout');


    publicWidget.registry.websiteSalePaymentTerms = publicWidget.Widget.extend({
        selector: '.oe_payment_terms',
        events: {
            "click input[name='payment_term_id']": '_onPaymentTermClick',
            "click #btn_accept_payment_terms": '_acceptPaymentTerms',
            "click #btn_deny_payment_terms": '_denyPaymentTerms',
        },

        /**
         * @override
         */
        start: function () {
            console.log('Payment Terms V10.4');
            return this._super.apply(this, arguments).then(function () {
                var available_term = $('input[name="payment_term_id"]').length;
                if (available_term > 0) {
                    var $payButton = $('#o_payment_form_pay');
                    $payButton.prop('disabled', true);
                    var disabledReasons = $payButton.data('disabled_reasons') || {};
                    if ($('input[name="payment_term_id"][checked]')) {
                        disabledReasons.payment_terms_selection = false;
                    } else {
                        disabledReasons.payment_terms_selection = true;
                    }
                    $payButton.data('disabled_reasons', disabledReasons);
                    $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
                }
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {object} ev
         */
        _onPaymentTermClick: function (ev) {
            $('#o_payment_form_pay').prop('disabled', true);
            var payment_term_id = $(ev.currentTarget).val();
            var values = {'payment_term_id': payment_term_id};
            dp.add(this._rpc({
                'route': '/shop/update_payment_term',
                'params': values,
            }).then(this._onPaymentTermUpdateAnswer.bind(this)));
        },

        /**
         * Update the total cost according to the selected shipping method
         * 
         * @private
         * @param {float} amount : The new total amount of to be paid
         */
        _updatePaymentAmount: function(amount){
            core.bus.trigger('update_shipping_cost', amount);
        },
        /**
         * Show amount due if operation is a success
         *
         * @private
         * @param {Object} result
         */
        _onPaymentTermUpdateAnswer: function (result) {
            if (!result.error) {
                // Get Payment Term note/description for modal
                var note = $.parseHTML(result.note);
                if (!$(note).text()) {
                    note = $.parseHTML('<p>' + result.payment_term_name + '</p>');
                }

                // Change forms based on order payment requirement
                $('#order_due_today .monetary_field').html(result.amount_due_today_html);
                if(result.amount_due_today == 0.0) {
                    $('#payment_method').hide();
                    $('#non_payment_method').show();
                } else {
                    this._updatePaymentAmount(result.amount_due_today);
                    $('#payment_method').show();
                    $('#non_payment_method').hide();
                }

                // Open success modal with message
                $('#payment_term_success_modal .success-modal-note').html(note);
                $('#payment_term_success_modal').modal();
            } else {
                // Open error modal
                console.error(result);
                $('#payment_term_error_modal').modal();
            }
        },

        /*
         * @private
         */
        _acceptPaymentTerms: function () {
            var $payButton = $('#o_payment_form_pay');
            var disabledReasons = $payButton.data('disabled_reasons') || {};
            disabledReasons.payment_terms_selection = false;
            $payButton.data('disabled_reasons', disabledReasons);
            $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
        },

        /*
         * @private
         */
        _denyPaymentTerms: function () {
            window.location = '/shop/reject_term_agreement';
        },
    });


    // update amount due after delivery options change
    publicWidget.registry.websiteSaleDelivery.include({
        _handleCarrierUpdateResult: function (result) {
            this._super.apply(this, arguments);
            if (result.amount_due_today_raw !== undefined) {
                this._updateShippingCost(result.amount_due_today_raw);
                $('#order_due_today .monetary_field').html(result.amount_due_today);
            }
        },
    });

    return publicWidget.registry.websiteSalePaymentTerms;
});
