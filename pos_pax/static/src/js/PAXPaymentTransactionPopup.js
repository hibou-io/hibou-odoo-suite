odoo.define('pos_pax.PAXPaymentTransactionPopup', function(require) {
    'use strict';

    // Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

    const { useState } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class PAXPaymentTransactionPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ message: '', confirmButtonIsShown: false });
            this.props.transaction.then(data => {
                if (data.auto_close) {
                    setTimeout(() => {
                        this.confirm();
                    }, 2000)
                } else {
                    this.state.confirmButtonIsShown = true;
                }
                this.state.message = data.message;
            }).progress(data => {
                this.state.message = data.message;
            })
        }
    }
    PAXPaymentTransactionPopup.template = 'PAXPaymentTransactionPopup';
    PAXPaymentTransactionPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'PAX Online Payment',
        body: '',
    };

    Registries.Component.add(PAXPaymentTransactionPopup);

    return PAXPaymentTransactionPopup;
});
