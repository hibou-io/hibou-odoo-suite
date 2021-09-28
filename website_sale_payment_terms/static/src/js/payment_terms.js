odoo.define('website_sale_payment_terms.payment_terms', function (require) {
    "use strict";

    require('web.dom_ready');
    var concurrency = require('web.concurrency');
    var core = require('web.core');
    var dp = new concurrency.DropPrevious();
    var publicWidget = require('web.public.widget');
    require('website_sale_delivery.checkout');


    console.log('Payment Terms V10.2');

    publicWidget.registry.websiteSalePaymentTerms = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            "click #payment_terms input[name='payment_term_id']": '_onPaymentTermClick',
            "click #btn_accept_payment_terms": '_acceptPaymentTerms',
            "click #btn_deny_payment_terms": '_denyPaymentTerms',
        },

        /**
         * @override
         */
        start: function () {
            core.bus.on('payment_terms_update_amount', this, this.updateAmountDue);
            return this._super.apply(this, arguments).then(function () {
                var available_term = $('input[name="payment_term_id"]').length;
                var $payButton = $('#o_payment_form_pay');
                if (available_term > 0) {
                    console.log('Payment term detected');
                    $payButton.prop('disabled', true);
                    var disabledReasons = $payButton.data('disabled_reasons') || {};
                    disabledReasons.payment_terms_selection = true;
                    $payButton.data('disabled_reasons', disabledReasons);
                } else {
                    console.log('no payment term detected');
                }
            });
        },

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        /*
         * Calculate amount Due Now
         *
         * @public
         * @param: {number} t Total
         * @param: {number} d Deposit percentage
         * @param: {number} f Deposit flat amount
         */
        calculateDeposit: function (t, d, f) {
            var amount = t * d / 100 + f;
            if (amount > 0) {
                amount = amount.toFixed(2);
                amount = amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                return amount;
            } else {
                amount = 0.00;
                return amount;
            }
        },

        /*
         * All input clicks update due amount
         *
         * @public
         */
        updateAmountDue: function () {
            var amount_total = $('#order_total span.oe_currency_value').html().replace(',', '');
            amount_total = parseFloat(amount_total);
            var $checked = $('input[name="payment_term_id"]:checked');
            var $deposit_percentage = $checked.attr('data-deposit-percentage');
            var $deposit_flat = parseFloat($checked.attr('data-deposit-flat'));
            var $due_amount = this.calculateDeposit(amount_total, $deposit_percentage, $deposit_flat);
            $('#order_due_today span.oe_currency_value').html($due_amount);
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
         * Show amount due if operation is a success
         *
         * @private
         * @param {Object} result
         */
        _onPaymentTermUpdateAnswer: function (result) {
            if (!result.error) {

                // Get Payment Term note/description for modal
                var note = result.note;
                if (!result.note) {
                    note = result.payment_term_name;
                }

                // Change forms based on order payment requirement
                this.updateAmountDue();
                if(!result.require_payment) {
                    $('#payment_method').hide();
                    $('#non_payment_method').show();
                    $('#order_due_today').hide();
                } else {
                    $('#payment_method').show();
                    $('#non_payment_method').hide();
                    $('#order_due_today').show();
                }

                // Open success modal with message
                $('#payment_term_success_modal .success-modal-note').text(note);
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
            core.bus.trigger('payment_terms_update_amount');
        },
    });

    return publicWidget.registry.websiteSalePaymentTerms;
});
