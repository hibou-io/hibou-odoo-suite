odoo.define('base_section_subtotal.widgets', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var SectionAndNoteListRenderer = require('account.section_and_note_backend');

SectionAndNoteListRenderer.include({
    /**
     * We want section and note to take the whole line (except handle and trash)
     * to look better and to hide the unnecessary fields.
     *
     * Hibou Section Subtotal
     * Utilize new XML attribute on tree views 'section-subtotal-field' to determine
     * if we should short the 'name' field and which field to display.
     *
     * Note that we support more than one field, but it will not line up correctly...
     *
     * @override
     */
    _renderBodyCell: function (record, node, index, options) {
        var $cell = this._super.apply(this, arguments);

        var isSection = record.data.display_type === 'line_section';

        if (isSection && this.arch.attrs['section-subtotal-field']) {
            var sectionSubtotalFields = this.arch.attrs['section-subtotal-field'].split(',');
            if (node.attrs.name === "name") {
                // duplicate some logic
                var nbrColumns = this._getNumberOfCols();
                if (this.handleField) {
                    nbrColumns--;
                }
                if (this.addTrashIcon) {
                    nbrColumns--;
                }
                // for the section subtotal field(s)
                nbrColumns -= sectionSubtotalFields.length;
                $cell.attr('colspan', nbrColumns);
            } else if (sectionSubtotalFields.indexOf(node.attrs.name) >= 0) {
                $cell.removeClass('o_hidden');
                return $cell;
            }
        }

        return $cell;
    },
});

basic_fields.NumericField.include({
    init: function () {
        this._super.apply(this, arguments);
        this._setSectionSubtotal();
    },

    _reset: function () {
        this._super.apply(this, arguments);
        this._setSectionSubtotal();
    },

    _setSectionSubtotal: function () {
        // line_sections will have empty fields, will update dynamically but not write them
        if (this.record.data['display_type'] === 'line_section') {
            var sequence = this.record.data.sequence;
            var id = this.record.data.id;
            if (this['__parentedParent'] && this.__parentedParent['state'] && this.__parentedParent.state['data']) {
                var all_rows = this.__parentedParent.state.data;
                var subtotal = 0.0;
                var self_found = false;
                for (var i = 0; i < all_rows.length; i++) {
                    var row = all_rows[i].data;
                    if (row.id == id) {
                        self_found = true;
                        continue;
                    }
                    if (self_found && row.sequence >= sequence) {
                        if (row.display_type === 'line_section' && row.id != id) {
                            break;
                        }
                        subtotal += row[this.name];
                    }
                }
                this.value = subtotal;
            }
        }
    },
});

});
