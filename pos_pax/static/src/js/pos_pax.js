odoo.define('pos_pax.pos_pax', function (require) {
"use strict";

// Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

const pos_model = require('point_of_sale.models');

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
    },
});

var _order_super = pos_model.Order.prototype;
pos_model.Order = pos_model.Order.extend({
    electronic_payment_in_progress: function() {
        var res = _order_super.electronic_payment_in_progress.apply(this, arguments);
        return res || this.get_paymentlines().some(line => line.pax_txn_pending);
    },
});

});
