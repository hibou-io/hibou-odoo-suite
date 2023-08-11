odoo.define('website_sale_payment_terms.payment_terms', function (require) {
    "use strict";

    require('web.dom_ready');
    const concurrency = require('web.concurrency');
    const core = require('web.core');
    
    const publicWidget = require('web.public.widget');
    require('website_sale_delivery.checkout');


    publicWidget.registry.websiteSalePaymentTerms = publicWidget.Widget.extend({
        selector: '.oe_payment_terms',
        events: {
            "click input[name='payment_term_id']": '_onPaymentTermClick',
            "click #btn_accept_payment_terms": '_acceptPaymentTerms',
        },
        
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.dp = new concurrency.DropPrevious();
        },

        /**
         * @override
         */
        start: async function () {
            const res = await this._super.apply(this, arguments)
            const available_term = $('input[name="payment_term_id"]').length;
            if (available_term > 0) {
                const $payButton = $('button[name="o_payment_submit_button"]');
                $payButton.prop('disabled', true);
                const disabledReasons = $payButton.data('disabled_reasons') || {};
                if ($('input[name="payment_term_id"]:checked').length > 0) {
                    disabledReasons.payment_terms_selection = false;
                } else {
                    disabledReasons.payment_terms_selection = true;
                }
                $payButton.data('disabled_reasons', disabledReasons);
                $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));
            }
            return res;
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {object} ev
         */
        _onPaymentTermClick: async function (ev) {
            ev.preventDefault();
            $('button[name="o_payment_submit_button"]').prop('disabled', true);
            // Get Payment Term note/description for modal
            const selected_term = $(ev.currentTarget);
            let note = $.parseHTML(selected_term.data('note'));
            if (!$(note).text()) {
                note = $.parseHTML('<p>' + selected_term.data('name') + '</p>');
            }
            // Open agreement modal with message
            $('#payment_term_agreement_modal .success-modal-note').html(note);
            $('#btn_accept_payment_terms').data('payment_term_id', selected_term.val());
            const modal = new Modal($('#payment_term_agreement_modal'));
            await modal.show();
        },

        /**
         * Set terms on the order
         *
         * @private
         * @param {Object} result
         */
        _acceptPaymentTerms: function (ev) {
            const payment_term_id = $(ev.currentTarget).data('payment_term_id');
            if (payment_term_id) {
                this.dp.add(this._rpc({
                    'route': '/shop/update_payment_term',
                    'params': {'payment_term_id': payment_term_id},
                }).then(this._onPaymentTermUpdateAmount.bind(this)));
            }
        },
        
        /**
         * Update amount on the page
         * 
         * @param {Object} result 
         */
        _onPaymentTermUpdateAmount: function(result) {
            if (result.error) {
                // Open error modal
                console.error(result.error);
                $('#payment_term_error_modal').modal();
            } else {
                // Change forms based on order payment requirement
                $('input[name="payment_term_id"]').filter(
                    (i, e)=>e.value==result.payment_term_id
                ).prop('checked', true);
                $('#order_due_today .monetary_field').html(result.amount_due_today_html);
                if(result.amount_due_today == 0.0) {
                    $('#payment_method').hide();
                    $('#non_payment_method').show();
                } else {
                    // Update the total cost according to the selected shipping method
                    core.bus.trigger('update_shipping_cost', result.amount_due_today);
                    $('#payment_method').show();
                    $('#non_payment_method').hide();
                }
                const $payButton = $('button[name="o_payment_submit_button"]');
                const disabledReasons = $payButton.data('disabled_reasons') || {};
                disabledReasons.payment_terms_selection = false;
                $payButton.data('disabled_reasons', disabledReasons);
                $payButton.prop('disabled', _.contains($payButton.data('disabled_reasons'), true));              
            }
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
