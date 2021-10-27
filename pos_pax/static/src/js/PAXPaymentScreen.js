odoo.define('pos_pax.PAXPaymentScreen', function (require) {
    'use strict';

    // Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

    const { _t } = require('web.core');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const PAX = require('pos_pax.pax_device');

    PAX.mDestinationIP = '';

    const PAXPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
                // tempting to use 'send-payment-request',
                // but method implements things that don't seem to exist yet (payment_method.payment_terminal)
                useListener('pax-send-payment-request', this._sendPAXPaymentRequest);
                useListener('pax-send-payment-request-debit', this._sendPAXPaymentRequestDebit);
            }

            async _sendPAXPaymentRequest({ detail: line }) {
                this.pax_credit_transaction(line, 'credit');
            }

            async _sendPAXPaymentRequestDebit({ detail: line }) {
                this.pax_credit_transaction(line, 'debit');
            }

            pax_credit_transaction(line, tender_type) {
                var order = this.env.pos.get_order();

                if(this.env.pos.getPAXOnlinePaymentJournals().length === 0) {
                    return;
                }

                var self = this;
                var transaction = {};

                var purchase_amount = line.get_amount();

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
                        ClerkID: this.env.pos.user.name,
                    },
                    traceInformation: {
                        ReferenceNumber: self.env.pos.get_order().uid,
                        // InvoiceNumber: self.env.pos.get_order().uid,
                    },
                }

                var def = new $.Deferred();

                // show the transaction popup.
                // the transaction deferred is used to update transaction status
                self.showPopup('PAXPaymentTransactionPopup', {
                    transaction: def
                });
                def.notify({
                    message: _t('Handling transaction...'),
                });

                PAX.mDestinationIP = self.env.pos.config.pax_endpoint;
                PAX[(tender_type == 'debit') ? 'DoDebit' : 'DoCredit'](transaction, function (response) {
                    console.log(response);
                    var parsed_response = self.env.pos.decodePAXResponse(response);
                    if (parsed_response.fail) {
                        def.resolve({message: parsed_response.fail})
                        return;
                    }
                    if (parsed_response.success) {
                        line.paid = true;
                        line.pax_card_number = parsed_response.card_num;
                        line.pax_txn_id = parsed_response.txn_id;
                        line.pax_approval = parsed_response.approval;
                        line.pax_txn_pending = false;
                        line.pax_tender_type = tender_type;
                        line.set_credit_card_name();
                        order.trigger('change', order);
                        self.render();
                        def.resolve({message: 'Approval ' + parsed_response.approval, auto_close: true})
                    }
                    def.resolve({message: _t('Unknown response.')})
                }, function (fail){
                    def.resolve({message: _t('Communication Failure: ') + fail});
                });
            }

            pax_do_reversal(line) {
                var def = new $.Deferred();
                var self = this;
                var transaction = {};

                // show the transaction popup.
                // the transaction deferred is used to update transaction status
                this.showPopup('PAXPaymentTransactionPopup', {
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
                        ClerkID: this.env.pos.user.name,
                    },
                    traceInformation: {
                        ReferenceNumber: this.env.pos.get_order().uid,
                        InvoiceNumber: '',
                        AuthCode: line.pax_approval,
                        TransactionNumber: line.pax_txn_id,
                    },
                }

                PAX.mDestinationIP = self.env.pos.config.pax_endpoint;
                PAX[(line.pax_tender_type == 'debit') ? 'DoDebit' : 'DoCredit'](transaction, function (response) {
                    var parsed_response = self.env.pos.decodePAXResponse(response);
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
            }

            remove_paymentline_by_ref(line) {
                this.env.pos.get_order().remove_paymentline(line);
                this.render();
            }

            /**
             * @override
             */
            deletePaymentLine(event) {
                const { cid } = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);
                if (line.pax_txn_id) {
                    this.pax_do_reversal(line);
                } else {
                    super.deletePaymentLine(event);
                }
            }

            /**
             * @override
             */
            addNewPaymentLine({ detail: paymentMethod }) {
                const order = this.env.pos.get_order();
                const res = super.addNewPaymentLine(...arguments);
                if (res && paymentMethod.use_payment_terminal == 'pax') {
                    order.selected_paymentline.pax_txn_pending = true;
                    order.trigger('change', order);
                    this.render();
                }
            }

        };

    Registries.Component.extend(PaymentScreen, PAXPaymentScreen);

    return PAXPaymentScreen;
});
