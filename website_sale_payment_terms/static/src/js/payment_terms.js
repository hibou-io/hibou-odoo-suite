odoo.define('website_sale_payment_terms.payment_terms', function (require) {
    "use strict";

    require('web.dom_ready');
    var ajax = require('web.ajax');
    var concurrency = require('web.concurrency');
    var dp = new concurrency.DropPrevious();
    var publicWidget = require('web.public.widget');
    require('website_sale_delivery.checkout');


    console.log('Payment Terms V10.1');

    var available_term = $('input[name="payment_term_id"]').length;
    if (available_term > 0) {
        console.log('Payment term detected');
        // Detect pay button and disable on page load - This isn't ideal but there is something I cant find that is preventing disabling this
        setTimeout(function(){ $('#o_payment_form_pay').prop('disabled', true); }, 500);
    } else {
        console.log('no payment term detected');
    }

    // Calculate amount Due Now
    function calculate_deposit(t, d, f) {
        var amount = t * d / 100 + f;
        if (amount > 0) {
            amount = amount.toFixed(2);
            amount = amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            return amount;
        } else {
            amount = 0.00;
            return amount;
        }
    }

    // Payment input clicks update sale.order payment_term_id
    var _onPaymentTermClick = function (ev) {
        $('#o_payment_form_pay').prop('disabled', true);
        var payment_term_id = $(ev.currentTarget).val();
        var values = {'payment_term_id': payment_term_id};
        dp.add(ajax.jsonRpc('/shop/update_payment_term', 'call', values).then(_onPaymentTermUpdateAnswer));
    };
    var $payment_terms = $("#payment_terms input[name='payment_term_id']");
    $payment_terms.click(_onPaymentTermClick);


    // All input clicks update due amount
    function updateAmountDue() {
        var $amount_total = $('#order_total span.oe_currency_value').html().replace(',', '');
        $amount_total = parseFloat($amount_total);
        var $checked = $('input[name="payment_term_id"]:checked');
        var $deposit_percentage = $checked.attr('data-deposit-percentage');
        var $deposit_flat = parseFloat($checked.attr('data-deposit-flat'));
        var $due_amount = calculate_deposit($amount_total, $deposit_percentage, $deposit_flat);
        $('#order_due_today span.oe_currency_value').html($due_amount);
    }

    // update amount due after delivery options change
    publicWidget.registry.websiteSaleDelivery.include({
        _handleCarrierUpdateResult: function (result) {
            this._super.apply(this, arguments);
            updateAmountDue();
        },
    });

    // Show amount due if operation is a success
    var _onPaymentTermUpdateAnswer = function (result) {
        if (!result.error) {

            // Get Payment Term note/description for modal
            var note = result.note;
            if (!result.note) {
                note = result.payment_term_name;
            }

            // Change forms based on order payment requirement
            updateAmountDue();
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
    };

});

function deny_payment_terms() {
    $('#o_payment_form_pay').prop('disabled', true);
    window.location = '/shop/reject_term_agreement';
}

function accept_payment_terms() {
    $('#o_payment_form_pay').prop('disabled', false);
}
