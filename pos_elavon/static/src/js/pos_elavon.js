odoo.define('pos_elavon.pos_elavon', function (require) {
"use strict";

var core    = require('web.core');
var rpc    = require('web.rpc');
var screens = require('point_of_sale.screens');
var gui     = require('point_of_sale.gui');
var pos_model = require('point_of_sale.models');

var _t      = core._t;

var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;
var PopupWidget = require('point_of_sale.popups');
var ScreenWidget = screens.ScreenWidget;
var PaymentScreenWidget = screens.PaymentScreenWidget;

pos_model.load_fields("account.journal", "pos_elavon_config_id");

pos_model.PosModel = pos_model.PosModel.extend({

    getOnlinePaymentJournals: function () {
        var self = this;
        var online_payment_journals = [];

        $.each(this.journals, function (i, val) {
            if (val.pos_elavon_config_id) {
                online_payment_journals.push({label:self.getCashRegisterByJournalID(val.id).journal_id[1], item:val.id});
            }
        });
        return online_payment_journals;
    },

    getCashRegisterByJournalID: function (journal_id) {
        var cashregister_return;

        $.each(this.cashregisters, function (index, cashregister) {
            if (cashregister.journal_id[0] === journal_id) {
                cashregister_return = cashregister;
            }
        });

        return cashregister_return;
    },

    decodeMagtek: function (s) {
        if (s.indexOf('%B') < 0) {
            return 0;
        }
        var to_return = {};
        to_return['ssl_card_number'] = s.substr(s.indexOf('%B') + 2, s.indexOf('^') - 2);
        var temp = s.substr(s.indexOf('^') + 1, s.length);
        name = temp.substr(0, temp.indexOf('/'));
        var exp = temp.substr(temp.indexOf('^') + 1, 4);
        to_return['ssl_exp_date'] = exp.substr(2, 2) + exp.substr(0, 2)
        to_return['ssl_card_present'] = 'Y'
        to_return['ssl_track_data'] = s
        return to_return
    },

    decodeElavonResponse: function (data) {
        var lines = data.split(/\r?\n/);
        var to_return = {}

        lines.forEach(function (line){
            var eq = line.indexOf('=');
            if (eq > 0) {
                var name = line.substr(0, eq);
                var value = line.substr(eq+1);
                to_return[name] = value;
            }
        });
        return to_return;
    }
});

var _paylineproto = pos_model.Paymentline.prototype;
pos_model.Paymentline = pos_model.Paymentline.extend({
    init_from_JSON: function (json) {
        _paylineproto.init_from_JSON.apply(this, arguments);

        this.paid = true;
        this.elavon_swipe_pending = json.elavon_swipe_pending;
        this.elavon_card_number = json.elavon_card_number;
        this.elavon_card_brand = json.elavon_card_brand;
        this.elavon_txn_id = json.elavon_txn_id;

        this.set_credit_card_name();
    },
    export_as_JSON: function () {
        return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {
            paid: this.paid,
            elavon_swipe_pending: this.elavon_swipe_pending,
            elavon_card_number: this.elavon_card_number,
            elavon_card_brand: this.elavon_card_brand,
            elavon_txn_id: this.elavon_txn_id,
        });
    },
    set_credit_card_name: function () {
        if (this.elavon_card_number) {
            this.name = this.elavon_card_brand + ' ' + this.elavon_card_number;
        }
    }
});

// Popup to show all transaction state for the payment.
var PaymentTransactionPopupWidget = PopupWidget.extend({
    template: 'PaymentTransactionPopupWidget',
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
gui.define_popup({name:'payment-transaction', widget: PaymentTransactionPopupWidget});

// Popup to record manual CC entry
var PaymentManualTransactionPopupWidget = PopupWidget.extend({
    template: 'PaymentManualTransactionPopupWidget',
    show: function (options) {
        this._super(options);
        this.setup_transaction_callback();
    },
    setup_transaction_callback: function(){
        var self = this;
        this.options.transaction.then(function (data) {
            if (data.auto_close) {
                setTimeout(function () {
                    self.gui.close_popup();
                }, 2000);
            }
            self.$el.find('p.body').html(data.message);
        }).progress(function (data) {
            self.$el.find('p.body').html(data.message);
        });
    },
    click_confirm: function(){
        var values = {
            ssl_card_number: this.$('input[name="card_number"]').val(),
            ssl_exp_date: this.$('input[name="exp_date"]').val(),
            ssl_cvv2cvc2: this.$('input[name="cvv2cvc2"]').val(),
        };
        if ( this.options.transaction.state() != 'pending' ) {
            this.options.transaction = $.Deferred();
            this.setup_transaction_callback();
        }
        if( this.options.confirm ){
            this.options.confirm.call(this, values, this.options.transaction);
        }
    },
});
gui.define_popup({name:'payment-manual-transaction', widget: PaymentManualTransactionPopupWidget});

// On all screens, if a card is swipped, return a popup error.
ScreenWidget.include({
    credit_error_action: function () {
        this.gui.show_popup('error-barcode',_t('Go to payment screen to use cards'));
    },

    show: function () {
        this._super();
        if(this.pos.getOnlinePaymentJournals().length !== 0) {
            this.pos.barcode_reader.set_action_callback('credit', _.bind(this.credit_error_action, this));
        }
    }
});

// On Payment screen, allow electronic payments
PaymentScreenWidget.include({
    // Override init because it eats all keyboard input and we need it for popups...
    init: function(parent, options) {
        var self = this;
        this._super(parent, options);

        // This is a keydown handler that prevents backspace from
        // doing a back navigation. It also makes sure that keys that
        // do not generate a keypress in Chrom{e,ium} (eg. delete,
        // backspace, ...) get passed to the keypress handler.
        this.keyboard_keydown_handler = function(event){
            if (event.keyCode === 8 || event.keyCode === 46) { // Backspace and Delete
                // don't prevent delete if a popup is up
                if (self.gui.has_popup()) {
                    return;
                }
                event.preventDefault();

                // These do not generate keypress events in
                // Chrom{e,ium}. Even if they did, we just called
                // preventDefault which will cancel any keypress that
                // would normally follow. So we call keyboard_handler
                // explicitly with this keydown event.
                self.keyboard_handler(event);
            }
        };

        // This keyboard handler listens for keypress events. It is
        // also called explicitly to handle some keydown events that
        // do not generate keypress events.
        this.keyboard_handler = function(event){
            // On mobile Chrome BarcodeEvents relies on an invisible
            // input being filled by a barcode device. Let events go
            // through when this input is focused.
            if (self.gui.has_popup()) {
                return;
            }
            if (BarcodeEvents.$barcodeInput && BarcodeEvents.$barcodeInput.is(":focus")) {
                return;
            }

            var key = '';

            if (event.type === "keypress") {
                if (event.keyCode === 13) { // Enter
                    self.validate_order();
                } else if ( event.keyCode === 190 || // Dot
                            event.keyCode === 110 ||  // Decimal point (numpad)
                            event.keyCode === 188 ||  // Comma
                            event.keyCode === 46 ) {  // Numpad dot
                    key = self.decimal_point;
                } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                    key = '' + (event.keyCode - 48);
                } else if (event.keyCode === 45) { // Minus
                    key = '-';
                } else if (event.keyCode === 43) { // Plus
                    key = '+';
                }
            } else { // keyup/keydown
                if (event.keyCode === 46) { // Delete
                    key = 'CLEAR';
                } else if (event.keyCode === 8) { // Backspace
                    key = 'BACKSPACE';
                }
            }

            self.payment_input(key);
            event.preventDefault();
        };
    },
    // end init override...

    // How long we wait for the odoo server to deliver the response of
    // a Elavon transaction
    server_timeout_in_ms: 120000,

    // How many Elavon transactions we send without receiving a
    // response
    server_retries: 3,

    _get_swipe_pending_line: function () {
        var i = 0;
        var lines = this.pos.get_order().get_paymentlines();

        for (i = 0; i < lines.length; i++) {
            if (lines[i].elavon_swipe_pending) {
                return lines[i];
            }
        }

        return 0;
    },

    // Hunt around for an existing line by amount etc.
    _does_credit_payment_line_exist: function (amount, card_number, card_brand, card_owner_name) {
        var i = 0;
        var lines = this.pos.get_order().get_paymentlines();

        for (i = 0; i < lines.length; i++) {
            if (lines[i].get_amount() === amount &&
                lines[i].elavon_card_number === card_number &&
                lines[i].elavon_card_brand === card_brand) {
                return true;
            }
        }

        return false;
    },

    retry_elavon_transaction: function (def, response, retry_nr, can_connect_to_server, callback, args) {
        var self = this;
        var message = "";

        if (retry_nr < self.server_retries) {
            if (response) {
                message = "Retry #" + (retry_nr + 1) + "...<br/><br/>" + response.message;
            } else {
                message = "Retry #" + (retry_nr + 1) + "...";
            }
            def.notify({
                message: message
            });

            setTimeout(function () {
                callback.apply(self, args);
            }, 1000);
        } else {
            if (response) {
                // what?
                //message = "Error " + response.error + ": " + lookUpCodeTransaction["TimeoutError"][response.error] + "<br/>" + response.message;
            } else {
                if (can_connect_to_server) {
                    message = _t("No response from Elavon (Elavon down?)");
                } else {
                    message = _t("No response from server (connected to network?)");
                }
            }
            def.resolve({
                message: message,
                auto_close: false
            });
        }
    },

    // Handler to manage the card reader string
    credit_code_transaction: function (parsed_result, old_deferred, retry_nr) {
        var order = this.pos.get_order();

        if(this.pos.getOnlinePaymentJournals().length === 0) {
            return;
        }

        var self = this;
        var transaction = {};
        var swipe_pending_line = self._get_swipe_pending_line();
        var purchase_amount = 0;

        if (swipe_pending_line) {
            purchase_amount = swipe_pending_line.get_amount();
        } else {
            purchase_amount = self.pos.get_order().get_due();
        }

        // handle manual or swiped
        if (parsed_result.ssl_card_number) {
            transaction = parsed_result;
        } else {
            var decodedMagtek = self.pos.decodeMagtek(parsed_result.code);
            if (!decodedMagtek) {
                this.gui.show_popup('error', {
                    'title': _t('Could not read card'),
                    'body': _t('This can be caused by a badly executed swipe or by not having your keyboard layout set to US QWERTY (not US International).'),
                });
                return;
            }
            transaction = decodedMagtek;
        }

        var endpoint = 'do_payment';
        if (purchase_amount < 0.0) {
            purchase_amount = -purchase_amount;
            endpoint = 'do_credit';
        }

        transaction['ssl_amount'] = purchase_amount.toFixed(2);  // This is the format and type that Elavon is expecting
        transaction['ssl_invoice_number'] = self.pos.get_order().uid;
        transaction['journal_id'] = parsed_result.journal_id;

        var def = old_deferred || new $.Deferred();
        retry_nr = retry_nr || 0;

        // show the transaction popup.
        // the transaction deferred is used to update transaction status
        // if we have a previous deferred it indicates that this is a retry
        if (! old_deferred) {
            self.gui.show_popup('payment-transaction', {
                transaction: def
            });
            def.notify({
                message: _t('Handling transaction...'),
            });
        }

        rpc.query({
                model: 'pos_elavon.elavon_transaction',
                method: endpoint,
                args: [transaction],
            }, {
                timeout: self.server_timeout_in_ms,
            })
            .then(function (data) {
                // if not receiving a response from Elavon, we should retry
                if (data === "timeout") {
                    self.retry_elavon_transaction(def, null, retry_nr, true, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
                    return;
                }

                if (data === "not setup") {
                    def.resolve({
                        message: _t("Please setup your Elavon merchant account.")
                    });
                    return;
                }

                if (data === "internal error") {
                    def.resolve({
                        message: _t("Odoo error while processing transaction.")
                    });
                    return;
                }

                var result = self.pos.decodeElavonResponse(data);
                result.journal_id = parsed_result.journal_id;

                // Example error data:
                // errorCode=4025
                // errorName=Invalid Credentials
                // errorMessage=The credentials supplied in the authorization request are invalid.
                var approval_code = result.ssl_approval_code;
                if (endpoint == 'do_payment' && (!approval_code || !approval_code.trim())) {
                    def.resolve({
                        message: "Error (" + (result.ssl_result_message || result.errorName) + ")",
                        auto_close: false,
                    });
                }

                // handle ssl_approval_code (only seen empty ones so far)
                if (false /* duplicate transaction detected */) {
                    def.resolve({
                        message: result.ssl_result_message,
                        auto_close: true,
                    });
                }

                // any other edge cases or failures?

                if (result.ssl_result_message == 'APPROVAL' || result.ssl_result_message == 'PARTIAL APPROVAL') {
                    var order = self.pos.get_order();
                    if (swipe_pending_line) {
                        order.select_paymentline(swipe_pending_line);
                    } else {
                        order.add_paymentline(self.pos.getCashRegisterByJournalID(parsed_result.journal_id));
                    }
                    var amount = parseFloat(result.ssl_amount);
                    if (endpoint == 'do_credit') {
                        amount = -amount;
                    }
                    order.selected_paymentline.set_amount(amount);
                    order.selected_paymentline.paid = true;
                    order.selected_paymentline.elavon_swipe_pending = false;
                    order.selected_paymentline.elavon_card_number = result.ssl_card_number;
                    order.selected_paymentline.elavon_card_brand = result.ssl_card_short_description;
                    if (result.ssl_card_short_description) {
                        order.selected_paymentline.elavon_card_brand = result.ssl_card_short_description;
                    } else {
                        order.selected_paymentline.elavon_card_brand = result.ssl_card_type;
                    }
                    order.selected_paymentline.elavon_txn_id = result.ssl_txn_id;
                    // maybe approval code....
                    order.selected_paymentline.set_credit_card_name();

                    self.order_changes();
                    self.reset_input();
                    self.render_paymentlines();
                    order.trigger('change', order);
                    def.resolve({
                        message: result.ssl_result_message + ' : ' + order.selected_paymentline.elavon_txn_id,
                        auto_close: true,
                    });
                }

            }).fail(function (type, error) {
                self.retry_elavon_transaction(def, null, retry_nr, false, self.credit_code_transaction, [parsed_result, def, retry_nr + 1]);
            });
    },

    credit_code_cancel: function () {
        return;
    },

    credit_code_action: function (parsed_result) {
        var self = this;
        var online_payment_journals = this.pos.getOnlinePaymentJournals();

        if (online_payment_journals.length === 1) {
            parsed_result.journal_id = online_payment_journals[0].item;
            self.credit_code_transaction(parsed_result);
        } else { // this is for supporting another payment system like elavon
            this.gui.show_popup('selection',{
                title:   'Pay ' + this.pos.get_order().get_due().toFixed(2) + ' with : ',
                list:    online_payment_journals,
                confirm: function (item) {
                    parsed_result.journal_id = item;
                    self.credit_code_transaction(parsed_result);
                },
                cancel:  self.credit_code_cancel,
            });
        }
    },

    remove_paymentline_by_ref: function (line) {
        this.pos.get_order().remove_paymentline(line);
        this.reset_input();
        this.render_paymentlines();
    },

    do_reversal: function (line, is_voidsale, old_deferred, retry_nr) {
        var def = old_deferred || new $.Deferred();
        var self = this;
        retry_nr = retry_nr || 0;

        // show the transaction popup.
        // the transaction deferred is used to update transaction status
        this.gui.show_popup('payment-transaction', {
            transaction: def
        });

        // TODO Maybe do this, as it might be convenient to store the data in json and then do updates to it
        // var request_data = _.extend({
        //     'transaction_type': 'Credit',
        //     'transaction_code': 'VoidSaleByRecordNo',
        // }, line.elavon_data);


        // TODO Do we need these options?
        // var message = "";
        // var rpc_method = "";
        //
        // if (is_voidsale) {
        //     message = _t("Reversal failed, sending VoidSale...");
        //     rpc_method = "do_voidsale";
        // } else {
        //     message = _t("Sending reversal...");
        //     rpc_method = "do_reversal";
        // }

        var request_data = {
            'ssl_txn_id': line.elavon_txn_id,
            'journal_id': line.cashregister.journal_id[0],
        };

        if (! old_deferred) {
            def.notify({
                message: 'Sending reversal...',
            });
        }

        rpc.query({
                model: 'pos_elavon.elavon_transaction',
                method: 'do_reversal',
                args: [request_data],
            }, {
                timeout: self.server_timeout_in_ms
            })
            .then(function (data) {
                if (data === "timeout") {
                    self.retry_elavon_transaction(def, null, retry_nr, true, self.do_reversal, [line, is_voidsale, def, retry_nr + 1]);
                    return;
                }

                if (data === "internal error") {
                    def.resolve({
                        message: _t("Odoo error while processing transaction.")
                    });
                    return;
                }

                var result = self.pos.decodeElavonResponse(data);
                if (result.ssl_result_message == 'APPROVAL') {
                    def.resolve({
                        message: 'Reversal succeeded.'
                    });
                    self.remove_paymentline_by_ref(line);
                    return;
                }

                if (result.errorCode == '5040') {
                    // Already removed.
                    def.resolve({
                        message: 'Invalid Transaction ID. This probably means that it was already reversed.',
                    });
                    self.remove_paymentline_by_ref(line);
                    return;
                }

                def.resolve({
                    message: 'Unknown message check console logs. ' + result.ssl_result_message,
                });

            }).fail(function (type, error) {
                self.retry_elavon_transaction(def, null, retry_nr, false, self.do_reversal, [line, is_voidsale, def, retry_nr + 1]);
            });
    },

    click_delete_paymentline: function (cid) {
        var lines = this.pos.get_order().get_paymentlines();

        for (var i = 0; i < lines.length; i++) {
            if (lines[i].cid === cid && lines[i].elavon_txn_id) {
                this.do_reversal(lines[i], false);
                return;
            }
        }

        this._super(cid);
    },

    // make sure there is only one paymentline waiting for a swipe
    click_paymentmethods: function (id) {
        var order = this.pos.get_order();
        var cashregister = null;
        for (var i = 0; i < this.pos.cashregisters.length; i++) {
            if (this.pos.cashregisters[i].journal_id[0] === id){
                cashregister = this.pos.cashregisters[i];
                break;
            }
        }

        if (cashregister.journal.pos_elavon_config_id) {
            var pending_swipe_line = this._get_swipe_pending_line();

            if (pending_swipe_line) {
                this.gui.show_popup('error',{
                    'title': _t('Error'),
                    'body':  _t('One credit card swipe already pending.'),
                });
            } else {
                this._super(id);
                order.selected_paymentline.elavon_swipe_pending = true;
                this.render_paymentlines();
                order.trigger('change', order); // needed so that export_to_JSON gets triggered
            }
        } else {
            this._super(id);
        }
    },

    click_elavon_manual_transaction: function (id) {
        var self = this;
        var def = new $.Deferred();
        var pending_swipe_line = this._get_swipe_pending_line();
        if (!pending_swipe_line) {
            this.gui.show_popup('error',{
                'title': _t('Error'),
                'body':  _t('No swipe pending payment line for manual transaction.'),
            });
            return;
        }

        this.gui.show_popup('payment-manual-transaction', {
            transaction: def,
            confirm: function(card_details, deffered) {
                card_details.journal_id = pending_swipe_line.cashregister.journal.id;
                self.credit_code_transaction(card_details, deffered);
                def.notify({message: _t('Handling transaction...')});
            },
        });
    },

    show: function () {
        this._super();
        if (this.pos.getOnlinePaymentJournals().length !== 0) {
            this.pos.barcode_reader.set_action_callback('credit', _.bind(this.credit_code_action, this));
        }
    },

    render_paymentlines: function() {
        this._super();
        var self = this;
        self.$('.paymentlines-container').on('click', '.elavon_manual_transaction', function(){
            self.click_elavon_manual_transaction();
        });
    },

    // before validating, get rid of any paymentlines that are waiting
    // on a swipe.
    validate_order: function(force_validation) {
        if (this.pos.get_order().is_paid() && ! this.invoicing) {
            var lines = this.pos.get_order().get_paymentlines();

            for (var i = 0; i < lines.length; i++) {
                if (lines[i].elavon_swipe_pending) {
                    this.pos.get_order().remove_paymentline(lines[i]);
                    this.render_paymentlines();
                }
            }
        }

        this._super(force_validation);
    }
});

});
