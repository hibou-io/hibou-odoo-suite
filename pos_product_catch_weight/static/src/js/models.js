/* Copyright 2018 Tecnativa - David Vidal
   Copyright 2018 Hibou Corp. - Jared Kipe
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("pos_product_catch_weight.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var session = require("web.session");
    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    models.PosModel = models.PosModel.extend({
        get_lot: function (product, location_id) {
            var done = new $.Deferred();
            session.rpc("/web/dataset/search_read", {
                "model": "stock.quant",
                "domain": [
                    ["location_id", "=", location_id],
                    ["product_id", "=", product],
                    ["lot_id", "!=", false]],
                "fields": [
                    'lot_id',
                    'quantity',
                    'lot_catch_weight',
                    'lot_catch_weight_ratio',
                    'lot_catch_weight_uom_id',
                ]
            }, {'async': false}).then(function (result) {
                var product_quants = [];
                if (result.length) {
                    product_quants = result.records;
                }
                done.resolve(product_quants);
            });
            return done;
        },
    });

    var _orderline_super = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        compute_lot_lines: function(){
            var done = new $.Deferred();
            var compute_lot_lines = _orderline_super.compute_lot_lines.apply(this, arguments);
            this.pos.get_lot(this.product.id, this.pos.config.stock_location_id[0])
                .then(function (product_quants) {
                    compute_lot_lines.product_quants = product_quants;
                    done.resolve(compute_lot_lines);
                });
            return compute_lot_lines;
        },

        get_base_price:    function(){
            var rounding = this.pos.currency.rounding;
            var valid_product_lot = this.pack_lot_lines.get_valid_lots();
            var lot_ratio_sum = 0.0;

            for (var i=0; valid_product_lot && i < valid_product_lot.length; i++) {
                lot_ratio_sum += valid_product_lot[i].get('lot_catch_weight_ratio');
            }
            var qty = this.get_quantity();
            if (lot_ratio_sum != 0.0) {
                qty = lot_ratio_sum;
            }
            return round_pr(this.get_unit_price() * qty * (1 - this.get_discount()/100), rounding);
        },

        get_all_prices: function(){
            var valid_product_lot = this.pack_lot_lines.get_valid_lots();
            var lot_ratio_sum = 0.0;
            for (var i=0; valid_product_lot && i < valid_product_lot.length; i++) {
                lot_ratio_sum += valid_product_lot[i].get('lot_catch_weight_ratio');
            }
            var qty = this.get_quantity();
            var qty_ratio = 1.0
            if (lot_ratio_sum != 0.0) {
                qty_ratio = lot_ratio_sum / qty;
            }

            var price_unit = (this.get_unit_price() * qty_ratio) * (1.0 - (this.get_discount() / 100.0));

            var taxtotal = 0;

            var product =  this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                product_taxes.push(_.detect(taxes, function(t){
                    return t.id === el;
                }));
            });

            var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
            _(all_taxes.taxes).each(function(tax) {
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });

            return {
                "priceWithTax": all_taxes.total_included,
                "priceWithoutTax": all_taxes.total_excluded,
                "tax": taxtotal,
                "taxDetails": taxdetail,
            };
        },

    });

    //var _packlotline_super = models.Packlotline.prototype;
    models.Packlotline = models.Packlotline.extend({
        defaults: {
            lot_name: null,
            lot_catch_weight_ratio: 1.0,
            lot_catch_weight: 1.0,
            lot_catch_weight_uom_id: null,
        },

        set_quant: function(quant) {
            this.set({
                lot_name: _.str.trim(quant.lot_id[1]) || null,
                lot_catch_weight_ratio: quant.lot_catch_weight_ratio || 1.0,
                lot_catch_weight: quant.lot_catch_weight || 1.0,
                lot_catch_weight_uom_id: quant.lot_catch_weight_uom_id || null,
            });
        },

        set_lot_name: function(name){
            /*
            If you want to allow selling unknown lots:
            {
                lot_name : _.str.trim(name) || null,
                lot_catch_weight_ratio : 1.0,
                lot_catch_weight : 1.0,
                lot_catch_weight_uom_id : null,
            }
             */

            this.set({
                lot_name : _.str.trim(name) || null,
                lot_catch_weight_ratio : 9999.0,
                lot_catch_weight : 9999.0,
                lot_catch_weight_uom_id : [0, 'INVALID'],
            });
        },
    })

});
