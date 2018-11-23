/* Copyright 2018 Tecnativa - David Vidal
   Copyright 2018 Hibou Corp. - Jared Kipe
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("pos_product_catch_weight.chrome", function (require) {
    "use strict";

    var chrome = require("point_of_sale.chrome");

    chrome.Chrome.include({
        build_widgets: function () {
            var res = this._super.apply(this, arguments);
            var packlotline = this.gui.popup_instances.packlotline;
            // Add events over instanced popup
            var events = {
                "change .packlot-line-select": "lot_to_input",
            };
            packlotline.events = Object.assign(
                packlotline.events, events
            );
            // Add methods over instanced popup
            // Write the value in the corresponding input
            packlotline.lot_to_input = function (event) {
                var $select = $(event.target);
                var $option = this.$("select.packlot-line-select option");
                var $input = this.$el.find("input");
                if ($input.length) {
                    for (var i = 0; i < $input.length; i++) {
                        var $i = $input[i];
                        if (!$i.value || i + 1 == $input.length) {
                            $i.value = $select[0].value;
                            $i.blur();
                            $i.focus();
                        }
                    }
                }
                $option.prop('selected', function () {
                    return this.defaultSelected;
                });
            };

            packlotline.click_confirm = function(){
                var pack_lot_lines = this.options.pack_lot_lines;
                this.$('.packlot-line-input').each(function(index, el){
                    var cid = $(el).attr('cid'),
                        lot_name = $(el).val();
                    var pack_line = pack_lot_lines.get({cid: cid});
                    var quant = null;
                    for (var i = 0; i < pack_lot_lines.product_quants.length; i++) {
                        if (pack_lot_lines.product_quants[i].lot_id[1] == lot_name) {
                            quant = pack_lot_lines.product_quants[i];
                            break;
                        }
                    }
                    if (quant) {
                        pack_line.set_quant(quant);
                    } else {
                        pack_line.set_lot_name(lot_name);
                    }
                });
                pack_lot_lines.remove_empty_model();
                pack_lot_lines.set_quantity_by_lot();
                this.options.order.save_to_db();
                this.options.order_line.trigger('change', this.options.order_line);
                this.gui.close_popup();
            },

            this.gui.popup_instances.packlotline = packlotline;

            return res;
        },
    });

});
