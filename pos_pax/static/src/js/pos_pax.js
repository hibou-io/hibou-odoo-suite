odoo.define('pos_pax.pos_pax', function (require) {
"use strict";

// Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

var core = require('web.core');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var pos_model = require('point_of_sale.models');
var _t = core._t;
var PopupWidget = require('point_of_sale.popups');
var PaymentScreenWidget = screens.PaymentScreenWidget;
var PAX = require('pos_pax.pax_device');

PAX.mDestinationIP = '';

pos_model.PosModel = pos_model.PosModel.extend({

    getPAXOnlinePaymentJournals: function () {
        var online_payment_methods = [];

        $.each(this.payment_methods, function (i, payment_method) {
            if (payment_method.use_payment_terminal == 'pax') {
                online_payment_methods.push({label: payment_method.name, item: payment_method.id});
            }
        });
        return online_payment_methods;
    },

    decodePAXResponse: function (data) {
        var status = data[5];
        if (status == 'ABORTED') {
            return {fail: 'Transaction Aborted'};
        } else if (status == 'DECLINE') {
            return {fail: 'Transaction Declined or not Allowed'};
        } else if (status == 'COMM ERROR') {
            return {fail: 'Communication Error (e.g. could be your CC processor or internet)'}
        } else if (status == 'DEBIT ONLY, TRY ANOTHER TENDER') {
            return {fail: 'Card does not support Debit. Use Credit or switch cards.'}
        } else if (status == 'RECEIVE ERROR') {
            return {fail: 'Error receiving response. Try again?'}
        } else if (status == 'OK') {
            return {
                success: true,
                approval: data[6][2],
                txn_id: data[10][0],
                card_num: '***' + data[9][0],
            }
        }
        var response = 'Not handled response: ' + status;
        if (this.debug) {
            response += ' --------- Debug Data: ' + data;
        }
        return {fail: response};
    },
});

var _paylineproto = pos_model.Paymentline.prototype;
pos_model.Paymentline = pos_model.Paymentline.extend({
    init_from_JSON: function (json) {
        _paylineproto.init_from_JSON.apply(this, arguments);

        this.paid = json.paid;
        this.pax_txn_pending = json.pax_txn_pending;
        this.pax_card_number = json.pax_card_number;
        this.pax_approval = json.pax_approval;
        this.pax_txn_id = json.pax_txn_id;
        this.pax_tender_type = json.pax_tender_type;

        this.set_credit_card_name();
    },
    export_as_JSON: function () {
        return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {
            paid: this.paid,
            pax_txn_pending: this.pax_txn_pending,
            pax_card_number: this.pax_card_number,
            pax_approval: this.pax_approval,
            pax_txn_id: this.pax_txn_id,
            pax_tender_type: this.pax_tender_type,
        });
    },
    set_credit_card_name: function () {
        if (this.pax_card_number) {
            this.name = this.pax_card_number + ((this.pax_tender_type == 'debit') ? ' (Debit)' : ' (Credit)');
        }
    }
});

// Popup to show all transaction state for the payment.
var PAXPaymentTransactionPopupWidget = PopupWidget.extend({
    template: 'PAXPaymentTransactionPopupWidget',
    show: function (options) {
        var self = this;
        this._super(options);
        options.transaction.then(function (data) {
            if (data.auto_close) {
                setTimeout(function () {
                    self.gui.close_popup();
                }, 2000);
            } else {
                self.close();
                self.$el.find('.popup').append('<div class="footer"><div class="button cancel">Ok</div></div>');
            }

            self.$el.find('p.body').html(data.message);
        }).progress(function (data) {
            self.$el.find('p.body').html(data.message);
        });
    }
});
gui.define_popup({name:'pax-payment-transaction', widget: PAXPaymentTransactionPopupWidget});

PaymentScreenWidget.include({

    _get_pax_txn_pending_line: function () {
        var i = 0;
        var lines = this.pos.get_order().get_paymentlines();

        for (i = 0; i < lines.length; i++) {
            if (lines[i].pax_txn_pending) {
                return lines[i];
            }
        }

        return 0;
    },

    // Handler to manage the card reader string
    pax_credit_transaction: function (tender_type) {
        var order = this.pos.get_order();

        if(this.pos.getPAXOnlinePaymentJournals().length === 0) {
            return;
        }

        var self = this;
        var transaction = {};
        var pending_line = self._get_pax_txn_pending_line();
        if ( ! pending_line ) {
            console.log('no pending line found!');
            return;
        }

        var purchase_amount = pending_line.get_amount();

        var transactionType = '01';  // SALE
        if (purchase_amount < 0.0) {
            purchase_amount = -purchase_amount;
            transactionType = '02';  // RETURN
        }

        transaction = {
            command: (tender_type == 'debit') ? 'T02' : 'T00',
            version: '1.28',
            transactionType: transactionType,
            amountInformation: {
                TransactionAmount: (purchase_amount * 100) | 0,  // cast to integer
            },
            cashierInformation: {
                ClerkID: this.pos.user.name,
            },
            traceInformation: {
                ReferenceNumber: self.pos.get_order().uid,
                // InvoiceNumber: self.pos.get_order().uid,
            },
        }

        var def = new $.Deferred();

        // show the transaction popup.
        // the transaction deferred is used to update transaction status
        self.gui.show_popup('pax-payment-transaction', {
            transaction: def
        });
        def.notify({
            message: _t('Handling transaction...'),
        });

        PAX.mDestinationIP = self.pos.config.pax_endpoint;
        PAX[(tender_type == 'debit') ? 'DoDebit' : 'DoCredit'](transaction, function (response) {
            console.log(response);
            var parsed_response = self.pos.decodePAXResponse(response);
            if (parsed_response.fail) {
                def.resolve({message: parsed_response.fail})
                return;
            }
            if (parsed_response.success) {
                pending_line.paid = true;
                pending_line.pax_card_number = parsed_response.card_num;
                pending_line.pax_txn_id = parsed_response.txn_id;
                pending_line.pax_approval = parsed_response.approval;
                pending_line.pax_txn_pending = false;
                pending_line.pax_tender_type = tender_type;
                pending_line.set_credit_card_name();
                self.order_changes();
                self.reset_input();
                self.render_paymentlines();
                order.trigger('change', order);
                def.resolve({message: 'Approval ' + parsed_response.approval, auto_close: true})
            }
            def.resolve({message: _t('Unknown response.')})
        }, function (fail){
            def.resolve({message: _t('Communication Failure: ') + fail});
        });
    },

    remove_paymentline_by_ref: function (line) {
        this.pos.get_order().remove_paymentline(line);
        this.reset_input();
        this.render_paymentlines();
    },

    pax_do_reversal: function (line) {
        var def = new $.Deferred();
        var self = this;
        var transaction = {};

        // show the transaction popup.
        // the transaction deferred is used to update transaction status
        this.gui.show_popup('pax-payment-transaction', {
            transaction: def
        });
        def.notify({
            message: 'Sending reversal...',
        });

        transaction = {
            command: (line.pax_tender_type == 'debit') ? 'T02' : 'T00',
            version: '1.28',
            transactionType: (line.get_amount() > 0) ? '17' : '18',  // V/SALE, V/RETURN
            cashierInformation: {
                ClerkID: this.pos.user.name,
            },
            traceInformation: {
                ReferenceNumber: self.pos.get_order().uid,
                InvoiceNumber: '',
                AuthCode: line.pax_approval,
                TransactionNumber: line.pax_txn_id,
            },
        }

        PAX.mDestinationIP = self.pos.config.pax_endpoint;
        PAX[(line.pax_tender_type == 'debit') ? 'DoDebit' : 'DoCredit'](transaction, function (response) {
            var parsed_response = self.pos.decodePAXResponse(response);
            if (parsed_response.fail) {
                def.resolve({message: parsed_response.fail})
                return;
            }
            if (parsed_response.success) {
                def.resolve({
                    message: _t('Reversal succeeded.'),
                    auto_close: true,
                });
                self.remove_paymentline_by_ref(line);
                return;
            }
            def.resolve({message: _t('Unknown response.')})
        }, function (fail){
            def.resolve({message: _t('Communication Failure: ') + fail});
        });
    },

    click_delete_paymentline: function (cid) {
        var lines = this.pos.get_order().get_paymentlines();

        for (var i = 0; i < lines.length; i++) {
            if (lines[i].cid === cid && lines[i].pax_txn_id) {
                this.pax_do_reversal(lines[i]);
                return;
            }
        }

        this._super(cid);
    },

    // make sure there is only one paymentline waiting for a swipe
    click_paymentmethods: function (id) {
        var order = this.pos.get_order();
        var payment_method = this.pos.payment_methods_by_id[id]

        if (payment_method.use_payment_terminal == 'pax') {
            var pending_line = this._get_pax_txn_pending_line();

            if (pending_line) {
                this.gui.show_popup('error',{
                    'title': _t('Error'),
                    'body':  _t('One credit card txn already pending.'),
                });
            } else {
                this._super(id);
                order.selected_paymentline.pax_txn_pending = true;
                this.render_paymentlines();
                order.trigger('change', order); // needed so that export_to_JSON gets triggered
            }
        } else {
            this._super(id);
        }
    },

    click_pax_send_transaction: function (tender_type) {
        var pending_txn_line = this._get_pax_txn_pending_line();
        if (!pending_txn_line) {
            this.gui.show_popup('error',{
                'title': _t('Error'),
                'body':  _t('No pending payment line to send.'),
            });
            return;
        }
        this.pax_credit_transaction(tender_type);
    },

    render_paymentlines: function() {
        this._super();
        var self = this;
        self.$('.paymentlines-container').on('click', '.pax_send_transaction', function(){
            self.click_pax_send_transaction('credit');
        });
        self.$('.paymentlines-container').on('click', '.pax_send_transaction_debit', function(){
            self.click_pax_send_transaction('debit');
        });
    },

    // before validating, get rid of any paymentlines that are pending
    validate_order: function(force_validation) {
        if (this.pos.get_order().is_paid() && ! this.invoicing) {
            var lines = this.pos.get_order().get_paymentlines();

            for (var i = 0; i < lines.length; i++) {
                if (lines[i].pax_txn_pending) {
                    this.pos.get_order().remove_paymentline(lines[i]);
                    this.render_paymentlines();
                }
            }
        }

        this._super(force_validation);
    },

});

});
