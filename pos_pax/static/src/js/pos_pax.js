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
        if (data[5] == 'ABORTED') {
            return {fail: 'Transaction Aborted'};
        } else if (data[5] == 'OK') {
            return {
                success: true,
                approval: data[6][2],
                txn_id: data[10][0],
                card_num: '***' + data[9][0],
            }
        }
        return {fail: 'Unknown Response. ' + data};
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

        this.set_credit_card_name();
    },
    export_as_JSON: function () {
        return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {
            paid: this.paid,
            pax_txn_pending: this.pax_txn_pending,
            pax_card_number: this.pax_card_number,
            pax_approval: this.pax_approval,
            pax_txn_id: this.pax_txn_id,
        });
    },
    set_credit_card_name: function () {
        if (this.pax_card_number) {
            this.name = this.pax_card_number;
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
