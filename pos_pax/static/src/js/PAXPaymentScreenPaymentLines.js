odoo.define('pos_pax.PAXPaymentScreenPaymentLines', function (require) {
    'use strict';

    // Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

    const PaymentScreenPaymentLines = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');

    const PAXPaymentLines = (PaymentScreenPaymentLines) =>
        class extends PaymentScreenPaymentLines {
            /**
             * @override
             */
            selectedLineClass(line) {
                return Object.assign({}, super.selectedLineClass(line), {
                    o_pos_pax_txn_pending: line.pax_txn_pending,
                });
            }
            /**
             * @override
             */
            unselectedLineClass(line) {
                return Object.assign({}, super.unselectedLineClass(line), {
                    o_pos_pax_txn_pending: line.pax_txn_pending,
                });
            }
        };

    Registries.Component.extend(PaymentScreenPaymentLines, PAXPaymentLines);

    return PAXPaymentLines;
});
